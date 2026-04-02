import urllib.request
import tarfile
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def download_models():
    base_dir = r"c:\Users\Ritvik\Favorites\Jarvis\Backend\Vision\Models"
    os.makedirs(base_dir, exist_ok=True)
    
    # URLs for COCO SSD MobileNet V2 (80 classes)
    tar_url = "http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz"
    pbtxt_url = "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v2_coco_2018_03_29.pbtxt"
    
    tar_path = os.path.join(base_dir, "ssd_mobilenet_v2_coco_2018_03_29.tar.gz")
    pb_path = os.path.join(base_dir, "frozen_inference_graph.pb")
    pbtxt_path = os.path.join(base_dir, "model.pbtxt")
    
    print("Downloading ssd_mobilenet_v2_coco_2018_03_29.tar.gz...")
    urllib.request.urlretrieve(tar_url, tar_path)
    
    print("Extracting frozen_inference_graph.pb...")
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith("frozen_inference_graph.pb"):
                f = tar.extractfile(member)
                if f:
                    with open(pb_path, 'wb') as outfile:
                        outfile.write(f.read())
                break
                    
    print("Downloading config file (.pbtxt)...")
    urllib.request.urlretrieve(pbtxt_url, pbtxt_path)
    
    print("Cleaning up tar file...")
    if os.path.exists(tar_path):
        os.remove(tar_path)
        
    print("Download complete!")

if __name__ == "__main__":
    download_models()
