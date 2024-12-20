import os
import xml.etree.ElementTree as ET

from PIL import Image
from tqdm import tqdm

from utils.utils import get_classes
from utils.utils_map import get_coco_map, get_map
from yolo import YOLO

if __name__ == "__main__":
    '''
    Recall and Precision are not area-based concepts like AP, so the network's Recall and Precision values differ depending on the threshold (Confidence).
    By default, the Recall and Precision values calculated by this code correspond to a threshold (Confidence) of 0.5.

    Due to the limitations of the mAP calculation principle, the network needs to obtain nearly all prediction boxes when calculating mAP. This is necessary to calculate Recall and Precision values under different threshold conditions.
    Therefore, the number of boxes in the `map_out/detection-results/` text files generated by this code is generally more than those generated directly by `predict`. This aims to list all possible prediction boxes.
    '''
    #------------------------------------------------------------------------------------------------------------------#
    #   map_mode specifies the content calculated when running this file.
    #   map_mode = 0 represents the entire map calculation process, including obtaining prediction results, ground truth, and calculating VOC_map.
    #   map_mode = 1 represents obtaining only the prediction results.
    #   map_mode = 2 represents obtaining only the ground truth.
    #   map_mode = 3 represents calculating only VOC_map.
    #   map_mode = 4 represents calculating the current dataset's 0.50:0.95 map using the COCO toolbox. This requires obtaining prediction results, ground truth, and installing pycocotools.
    #-------------------------------------------------------------------------------------------------------------------#
    map_mode        = 0
    #--------------------------------------------------------------------------------------#
    #   classes_path specifies the classes for which VOC_map will be measured.
    #   Usually, this should be the same as the classes_path used during training and prediction.
    #--------------------------------------------------------------------------------------#
    classes_path    = 'model_data/target.txt'
    #--------------------------------------------------------------------------------------#
    #   MINOVERLAP specifies the desired mAP0.x. For the meaning of mAP0.x, please search online.
    #   For example, to calculate mAP0.75, set MINOVERLAP = 0.75.
    #
    #   When the overlap between a predicted box and a ground truth box exceeds MINOVERLAP, the predicted box is considered a positive sample; otherwise, it is a negative sample.
    #   Therefore, the higher the MINOVERLAP, the more accurate the predicted box needs to be to be considered a positive sample, and the lower the calculated mAP value.
    #--------------------------------------------------------------------------------------#
    MINOVERLAP      = 0.5
    #--------------------------------------------------------------------------------------#
    #   Due to the limitations of the mAP calculation principle, the network needs to obtain nearly all prediction boxes when calculating mAP.
    #   As a result, the confidence value should be set as low as possible to capture all potential prediction boxes.
    #
    #   This value is usually not adjusted. Since calculating mAP requires obtaining nearly all prediction boxes, the confidence here should not be arbitrarily changed.
    #   To obtain Recall and Precision values for different thresholds, modify the score_threhold below.
    #--------------------------------------------------------------------------------------#
    confidence      = 0.001
    #--------------------------------------------------------------------------------------#
    #   The value for non-maximum suppression used during prediction. The larger the value, the less strict the non-maximum suppression.
    #
    #   This value is usually not adjusted.
    #--------------------------------------------------------------------------------------#
    nms_iou         = 0.5
    #---------------------------------------------------------------------------------------------------------------#
    #   Recall and Precision are not area-based concepts like AP, so the network's Recall and Precision values differ depending on the threshold.
    #
    #   By default, the Recall and Precision values calculated by this code correspond to a threshold of 0.5 (defined as score_threhold here).
    #   Since calculating mAP requires nearly all prediction boxes, the confidence defined above should not be arbitrarily changed.
    #   Here, score_threhold is specifically defined to represent the threshold, allowing Recall and Precision values corresponding to the threshold to be found during mAP calculation.
    #---------------------------------------------------------------------------------------------------------------#
    score_threhold  = 0.5
    #-------------------------------------------------------#
    #   map_vis specifies whether to enable visualization for VOC_map calculation.
    #-------------------------------------------------------#
    map_vis         = False
    #-------------------------------------------------------#
    #   Path to the VOC dataset folder.
    #   Default points to the VOC dataset in the root directory.
    #-------------------------------------------------------#
    VOCdevkit_path  = 'VOCdevkit'
    #-------------------------------------------------------#
    #   Folder for output results, default is map_out.
    #-------------------------------------------------------#
    map_out_path    = 'map_out'

    image_ids = open(os.path.join(VOCdevkit_path, "VOC2007/ImageSets/Main/test.txt")).read().strip().split()

    if not os.path.exists(map_out_path):
        os.makedirs(map_out_path)
    if not os.path.exists(os.path.join(map_out_path, 'ground-truth')):
        os.makedirs(os.path.join(map_out_path, 'ground-truth'))
    if not os.path.exists(os.path.join(map_out_path, 'detection-results')):
        os.makedirs(os.path.join(map_out_path, 'detection-results'))
    if not os.path.exists(os.path.join(map_out_path, 'images-optional')):
        os.makedirs(os.path.join(map_out_path, 'images-optional'))

    class_names, _ = get_classes(classes_path)

    if map_mode == 0 or map_mode == 1:
        print("Load model.")
        yolo = YOLO(confidence = confidence, nms_iou = nms_iou)
        print("Load model done.")

        print("Get predict result.")
        for image_id in tqdm(image_ids):
            image_path  = os.path.join("D:\dataset\EggsofAlive\JPEGImages/"+image_id+".jpg")
            image       = Image.open(image_path)
            if map_vis:
                image.save(os.path.join(map_out_path, "images-optional/" + image_id + ".jpg"))
            yolo.get_map_txt(image_id, image, class_names, map_out_path)
        print("Get predict result done.")
        
    if map_mode == 0 or map_mode == 2:
        print("Get ground truth result.")
        for image_id in tqdm(image_ids):
            with open(os.path.join(map_out_path, "ground-truth/"+image_id+".txt"), "w") as new_f:
                root = ET.parse(os.path.join(VOCdevkit_path, "VOC2007/Annotations/"+image_id+".xml")).getroot()
                for obj in root.findall('object'):
                    difficult_flag = False
                    if obj.find('difficult') != None:
                        difficult = obj.find('difficult').text
                        if int(difficult) == 1:
                            difficult_flag = True
                    obj_name = obj.find('name').text
                    if obj_name not in class_names:
                        continue
                    bndbox  = obj.find('bndbox')
                    left    = bndbox.find('xmin').text
                    top     = bndbox.find('ymin').text
                    right   = bndbox.find('xmax').text
                    bottom  = bndbox.find('ymax').text

                    if difficult_flag:
                        new_f.write("%s %s %s %s %s difficult\n" % (obj_name, left, top, right, bottom))
                    else:
                        new_f.write("%s %s %s %s %s\n" % (obj_name, left, top, right, bottom))
        print("Get ground truth result done.")

    if map_mode == 0 or map_mode == 3:
        print("Get map.")
        get_map(MINOVERLAP, True, score_threhold = score_threhold, path = map_out_path)
        print("Get map done.")

    if map_mode == 4:
        print("Get map.")
        get_coco_map(class_names = class_names, path = map_out_path)
        print("Get map done.")
