# -*- coding: utf-8 -*-

from pkg_resources import resource_filename

def pose_predictor_model_location():
    return resource_filename(__name__, "models/retrained2022Shape_predictor_68.dat")

def pose_predictor_five_point_model_location():
    return resource_filename(__name__, "models/retrained2022Shape_predictor_5.dat")

def face_recognition_model_location():
    return resource_filename(__name__, "models/retrained2022Face_recognition_resnet.dat")

def cnn_face_detector_model_location():
    return resource_filename(__name__, "models/refitedMmod_human_face_detector.dat")

