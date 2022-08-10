# Real Face Extraction - Intel RealSense D435i
This application allows to distinguish a real photo from a fake one according to depth information captured with the D435i camera.  
It takes as input a .bag file and it provides a .jpg if the image inside the .bag file is real.

## [dmo.ipynb](https://github.com/MorphSeur/FaceExtractionIntelRealSense/blob/master/dmo.ipynb)
Two .bag files: real and fake image in a video, are recorded using [Intel RealSense Viewer](https://github.com/IntelRealSense/librealsense/releases/download/v2.50.0/Intel.RealSense.SDK-WIN10-2.50.0.3785.exe).  
Read and convert a .bag file, containting color and depth information, into [Color.avi]() and [Depth.avi]().  
[librealsense](https://github.com/MorphSeur/FaceExtractionIntelRealSense/blob/master/lissi_realsense), made by [Ali M.](https://github.com/modaresimr/lissi_realsense/tree/main/lissi_realsense), is exploited for the conversion.  
.dpo decoder is added.  
REST API is used for encapsulating the DMO.  

To run the application:
```sh
$ run the first cell of the jupyter notebook named dmo.ipynb
```

## Requirements
 - Download the [models](https://github.com/MorphSeur/faceRecognitionH2020_3/tree/master/lissilabmodels/models) necessary for the face detection and store them in [models](https://github.com/MorphSeur/FaceExtractionIntelRealSense/tree/master/lissilabmodels/models) (It is due to space in the Github account).  
 - .bag files (fake and real) are stored in a [NAS](/NAS/H2020/dmo) accessible locally.
 - Please install the [requirements.txt](https://github.com/MorphSeur/FaceExtractionIntelRealSense/blob/master/requirements.txt) by:
    ```sh
    $ pip install -r requirements.txt
    ```