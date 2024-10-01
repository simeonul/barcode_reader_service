import os
import cv2
import numpy as np

from scanners.decoding_util import DecodingUtil


class DetectionDecoding:

    @staticmethod
    def preprocess(image):
        dilate_kernel = np.ones(shape=(3, 20), dtype=np.uint8)
        grayscale_image = cv2.cvtColor(src=image, code=cv2.COLOR_BGR2GRAY)
        _, binary_image = cv2.threshold(src=grayscale_image, thresh=0, maxval=255, type=cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        revert_image = cv2.bitwise_not(src=binary_image)
        preprocessed = cv2.dilate(src=revert_image, kernel=dilate_kernel, iterations=1)
        #cv2.imwrite(os.path.join("results", "preprocessed.png"), preprocessed)
        return preprocessed

    @staticmethod
    def level_crop(x_coords, y_coords, rotated_rectangle, original_image, patch_index):
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        bounding_box_width = x_max - x_min
        bounding_box_height = y_max - y_min
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        width, height = rotated_rectangle[1]
        rotation_angle = rotated_rectangle[2]

        interest_region = cv2.getRectSubPix(image=original_image, patchSize=(bounding_box_width, bounding_box_height), center=(x_center, y_center))
        if rotation_angle != 90:
            # copy = interest_region.copy()
            # cv2.putText(copy, str(rotation_angle), (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
            # cv2.putText(copy, str(width), (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            # cv2.imwrite(os.path.join("results", f"patch_{patch_index}.png"), copy)
            if rotation_angle > 45:
                rotation_angle -= 90
            rotation_matrix = cv2.getRotationMatrix2D(center=(bounding_box_width / 2, bounding_box_height / 2), angle=rotation_angle, scale=1)
            horizontal_patch = cv2.warpAffine(src=interest_region, M=rotation_matrix, dsize=(bounding_box_width, bounding_box_height))
            if height > width:
                aux = width
                width = height
                height = aux
            # cv2.imwrite(os.path.join("results", f"patch_warped_{patch_index}.png"), horizontal_patch)
            horizontal_patch = cv2.getRectSubPix(image=horizontal_patch, patchSize=(int(width), int(height)),
                                                center=(bounding_box_width / 2, bounding_box_height / 2))
            return horizontal_patch
        return interest_region

    @staticmethod
    def get_probable_patches(original_image, preprocessed_image):
        patch_index = 0
        contours, _ = cv2.findContours(image=preprocessed_image, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)

        contour_points = original_image.copy()
        for contour in contours:
            for point in contour:
                x, y = point[0]
                for i in range(x - 1, x + 2):
                    for j in range(y - 1, y + 2):
                        if 0 <= i < contour_points.shape[1] and 0 <= j < contour_points.shape[0]:
                            contour_points[j, i] = [0, 255, 0]
        # cv2.imwrite(os.path.join("results", "contour_points.png"), contour_points)

        probable_patches = []
        box_points_image = original_image.copy()
        for contour in contours:
            rotated_rectangle = cv2.minAreaRect(contour)
            if rotated_rectangle[1][0] >= 40:
                rectangle_points = cv2.boxPoints(rotated_rectangle)
                rectangle_points = np.int0(rectangle_points)
                x_coordinates, y_coordinates = zip(*rectangle_points)
                # cv2.drawContours(box_points_image, [rectangle_points], 0, (0, 255, 0), 2)

                horizontal_patch = DetectionDecoding.level_crop(x_coordinates, y_coordinates, rotated_rectangle, original_image, patch_index)
                patch_index = patch_index + 1
                if horizontal_patch.shape[1] > 95:
                    probable_patches.append(horizontal_patch)
        # cv2.imwrite(os.path.join("results", "bounding_boxes.png"), box_points_image)
        return probable_patches

    @staticmethod
    def decode_candidate(candidate):
        grayscale = cv2.cvtColor(src=candidate, code=cv2.COLOR_BGR2GRAY)
        _, thresholded = cv2.threshold(src=grayscale, thresh=0, maxval=255, type=cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed = cv2.bitwise_not(src=thresholded)
        height = candidate.shape[0]
        barcode = None
        for row in range(height - 1):
            try:
                barcode = DetectionDecoding.decode_row(preprocessed[row])
            except Exception:
                pass
            if barcode is not None:
                return barcode
        return None

    @staticmethod
    def get_encoding(lengths):
        encoding = []
        for digit in range(0, len(lengths), 4):
            bar1, bar2, bar3, bar4 = lengths[digit:digit + 4]
            digit = DecodingUtil.decode_digit(bar1, bar2, bar3, bar4)
            encoding.append(digit)
        return encoding

    @staticmethod
    def validate(barcode):
        weights = [1, 3] * 6
        digit_sum = sum(int(barcode[i]) * weights[i] for i in range(12))
        checksum_digit = 0
        if (digit_sum % 10) != 0:
            checksum_digit = 10 - (digit_sum % 10)
        print(f"Checksum digit for {barcode}: {checksum_digit}")
        if checksum_digit == int(barcode[-1]):
            print("VALID")
            return True
        else:
            print("INVALID")
            return False

    @staticmethod
    def decode_row(row):
        lengths = DecodingUtil.row_to_lengths_array(row)
        left_patterns = lengths[0]
        right_patterns = lengths[1]
        left_side = None
        right_side = None
        if len(left_patterns) == 24:
            left_side = DetectionDecoding.get_encoding(left_patterns)
        if len(right_patterns) == 24:
            right_side = DetectionDecoding.get_encoding(right_patterns)

        if left_side is not None and right_side is not None:
            first_digit = DecodingUtil.decode_first_digit(left_side)
            left_digits = ''.join(i['digit'] for i in left_side)
            right_digits = ''.join(i['digit'] for i in right_side)
            barcode = first_digit + left_digits + right_digits
            if DetectionDecoding.validate(barcode):
                return barcode
        return None

    @staticmethod
    def decode(candidates):
        for i in range(len(candidates)):
            # cv2.imwrite(os.path.join("results", f"candidate_{i}.png"), candidates[i])
            barcode = DetectionDecoding.decode_candidate(candidates[i])
            if barcode is not None:
                return barcode
        return None

    @staticmethod
    def detect(initial_image):
        preprocessed_image = DetectionDecoding.preprocess(initial_image)
        # cv2.imwrite(os.path.join("results", "initial_image.png"), initial_image)
        candidates = DetectionDecoding.get_probable_patches(initial_image, preprocessed_image)
        return candidates

    @staticmethod
    def detect_decode(image):
        candidates = DetectionDecoding.detect(image)
        return DetectionDecoding.decode(candidates)
