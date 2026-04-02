import urllib.request
import tarfile
import os

def download_models():
    base_dir = r"c:\Users\Ritvik\Favorites\Jarvis\Backend\Vision\Models"
    os.makedirs(base_dir, exist_ok=True)
    
    # URLs for COCO SSD MobileNet V3 (80 classes)
    model_name = "ssd_mobilenet_v3_large_coco_2020_01_14"
    tar_url = f"http://download.tensorflow.org/models/object_detection/{model_name}.tar.gz"
    pbtxt_url = "https://gist.githubusercontent.com/dkurt/54a40c9241def01f2fde23631f47895e/raw/5ade97f3b49abda35c345b5c92c81fb377033cb2/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
    
    tar_path = os.path.join(base_dir, f"{model_name}.tar.gz")
    pb_path = os.path.join(base_dir, "frozen_inference_graph.pb")
    pbtxt_path = os.path.join(base_dir, "model.pbtxt")
    
    print(f"Downloading {model_name}.tar.gz...")
    urllib.request.urlretrieve(tar_url, tar_path)
    
    print("Extracting frozen_inference_graph.pb...")
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith("frozen_inference_graph.pb"):
                # Extract specifically this file and rename/move to base_dir
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
        
    print("Download complete! Models are ready in Backend/Vision/Models/")

if __name__ == "__main__":
    download_models()
