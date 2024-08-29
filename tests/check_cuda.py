import torch
import whisper

def check_cuda():
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    
    print(f"Whisper version: {whisper.__version__}")

    try:
        model = whisper.load_model("base")
        print("Whisper model loaded successfully")
        if torch.cuda.is_available():
            print("Moving model to CUDA...")
            model.to('cuda')
            print("Model moved to CUDA successfully")
    except Exception as e:
        print(f"Error loading Whisper model: {str(e)}")

if __name__ == "__main__":
    check_cuda()