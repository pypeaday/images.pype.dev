# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pyautogui",
#     "fastapi",
#     "uvicorn[standard]",
#     "python-multipart",
#     "Pillow",
#     "GitPython",
#     "toml",
# ]
# ///

# ]
# ///
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, Response # Added HTMLResponse, Response
from pathlib import Path
import uuid
import datetime
from PIL import Image
import io
import uvicorn # Added uvicorn
import toml # For reading config.toml

# Assuming utils.py is in the same directory (app)
# from .utils import commit_and_push_image

import git # GitPython library

def commit_and_push_image(repo_path: Path, image_file_path: Path, commit_message: str, auto_push: bool = False):
    """
    Adds, commits, and (optionally) pushes a new image to the Git repository.
    
    Args:
        repo_path: The local path to the Git repository.
        image_file_path: The path to the image file within the repository (e.g., repo_path / 'static' / 'image.png').
        commit_message: The commit message.
        
    Returns:
        A tuple (success: bool, message: str).
    """
    try:
        # Ensure repo_path is a valid directory
        if not repo_path.is_dir():
            return False, f"Repository path {repo_path} does not exist or is not a directory."

        # Initialize the repository object
        try:
            repo = git.Repo(repo_path)
        except git.InvalidGitRepositoryError:
            return False, f"Path {repo_path} is not a valid Git repository."
        except Exception as e:
            return False, f"Error initializing Git repository at {repo_path}: {str(e)}"

        # Ensure the image file is within the repository
        # image_file_path should be relative to the repo_path for git add
        try:
            relative_image_path = image_file_path.relative_to(repo_path)
        except ValueError:
            return False, f"Image file {image_file_path} is not within the repository path {repo_path}."

        # Check if the file exists before adding
        if not image_file_path.exists():
            return False, f"Image file {image_file_path} does not exist."

        # Add the image file to the staging area
        repo.index.add([str(relative_image_path)])
        
        # Commit the changes
        repo.index.commit(commit_message)
        
        push_message = ""
        if auto_push:
            try:
                # Attempt to push to the default remote (usually 'origin') and current branch
                # Ensure your environment is configured for passwordless push (e.g., SSH keys)
                # or Git credential helper.
                origin = repo.remote(name='origin') # Assumes remote is named 'origin'
                # You might want to specify the branch explicitly if it's not the current one
                # or if you want to push to a specific remote branch.
                # Example: origin.push(repo.head.reference)
                push_infos = origin.push()
                
                # Check push status
                # push_infos is a list of PushInfo objects. 
                # A successful push usually has flags like PushInfo.UP_TO_DATE or PushInfo.FAST_FORWARD
                # An error might have PushInfo.ERROR or PushInfo.REJECTED
                # This is a basic check; more robust error handling might be needed.
                if any(p.flags & (git.remote.PushInfo.ERROR | git.remote.PushInfo.REJECTED) for p in push_infos):
                    errors = [p.summary for p in push_infos if p.flags & (git.remote.PushInfo.ERROR | git.remote.PushInfo.REJECTED)]
                    push_message = f" Commit successful, but push failed: {'; '.join(errors)}"
                    # Potentially return False here if push is critical
                    # return False, f"Image '{relative_image_path}' committed, but push failed: {'; '.join(errors)}"
                else:
                    push_message = " and pushed successfully to remote."
            except git.GitCommandError as e:
                # This catches errors from the git command itself (e.g., remote not found, auth failure)
                push_message = f" Commit successful, but push failed: {str(e)}"
                # return False, f"Image '{relative_image_path}' committed, but push failed: {str(e)}"
            except Exception as e:
                # Catch other potential errors during push
                push_message = f" Commit successful, but an unexpected error occurred during push: {str(e)}"
                # return False, f"Image '{relative_image_path}' committed, but an unexpected error occurred during push: {str(e)}"
        
        return True, f"Image '{relative_image_path}' committed successfully{push_message}."

    except Exception as e:
        # Log the exception for debugging
        print(f"Error during Git operation: {e}")
        return False, f"An error occurred during Git operation: {str(e)}"

if __name__ == '__main__':
    # Example usage (for testing this script directly)
    # This requires a test git repository to be set up.
    print("This is a utility module for Git operations. It's meant to be imported.")
    # TEST_REPO_PATH = Path("/tmp/my_test_images_repo") # Create this repo for testing
    # TEST_REPO_PATH.mkdir(parents=True, exist_ok=True)
    # if not (TEST_REPO_PATH / ".git").exists():
    #     git.Repo.init(TEST_REPO_PATH)
    #     (TEST_REPO_PATH / "static").mkdir(exist_ok=True)
    #     print(f"Initialized test git repo at {TEST_REPO_PATH}")

    # # Create a dummy image file
    # dummy_image_name = "test_image.png"
    # dummy_image_path_abs = TEST_REPO_PATH / "static" / dummy_image_name
    # with open(dummy_image_path_abs, "w") as f:
    #     f.write("dummy image content")
    # print(f"Created dummy image: {dummy_image_path_abs}")

    # success, message = commit_and_push_image(
    #     repo_path=TEST_REPO_PATH,
    #     image_file_path=dummy_image_path_abs,
    #     commit_message="Test commit for dropper clone utils"
    # )
    # print(f"Commit success: {success}, Message: {message}")

    # # To test again, you might need to remove the dummy file or change its content
    # # dummy_image_path_abs.unlink(missing_ok=True)


# --- Configuration ---
CONFIG_FILE_PATH = Path("config.toml")

# Default configuration values
DEFAULT_IMAGES_REPO_PATH_STR = "."  # Assuming app runs in the root of the image repo
DEFAULT_IMAGE_SUB_DIR = "blog-media"
DEFAULT_GIT_AUTO_PUSH = False
DEFAULT_STATIC_IO_USER = "your_github_username" # Placeholder
DEFAULT_STATIC_IO_REPO = "your_images_repo_name" # Placeholder
DEFAULT_STATIC_IO_BRANCH = "main"

# Load configuration from TOML file
config = {}
if CONFIG_FILE_PATH.exists():
    try:
        config = toml.load(CONFIG_FILE_PATH)
    except toml.TomlDecodeError as e:
        print(f"Error decoding {CONFIG_FILE_PATH}: {e}. Using default configurations.")
        config = {}
else:
    print(f"{CONFIG_FILE_PATH} not found. Using default configurations and creating a template.")
    # Create a template config file if it doesn't exist
    template_config = {
        "title": "Shotput Configuration",
        "repository": {
            "images_repo_path": DEFAULT_IMAGES_REPO_PATH_STR,
            "image_sub_dir": DEFAULT_IMAGE_SUB_DIR,
            "git_auto_push": DEFAULT_GIT_AUTO_PUSH
        },
        "static_cdn": {
            "user": DEFAULT_STATIC_IO_USER,
            "repo": DEFAULT_STATIC_IO_REPO,
            "branch": DEFAULT_STATIC_IO_BRANCH
        }
    }
    try:
        with open(CONFIG_FILE_PATH, "w") as f:
            toml.dump(template_config, f)
        print(f"Created a template config file at {CONFIG_FILE_PATH}. Please review and update it.")
    except Exception as e:
        print(f"Could not create template config file: {e}")

# Get values from config, falling back to defaults
repo_config = config.get("repository", {})
cdn_config = config.get("static_cdn", {})

IMAGES_REPO_PATH_STR = repo_config.get("images_repo_path", DEFAULT_IMAGES_REPO_PATH_STR)
IMAGES_REPO_PATH = Path(IMAGES_REPO_PATH_STR)
IMAGE_SUB_DIR = repo_config.get("image_sub_dir", DEFAULT_IMAGE_SUB_DIR)
GIT_AUTO_PUSH = repo_config.get("git_auto_push", DEFAULT_GIT_AUTO_PUSH)

STATIC_IO_USER = cdn_config.get("user", DEFAULT_STATIC_IO_USER)
STATIC_IO_REPO = cdn_config.get("repo", DEFAULT_STATIC_IO_REPO)
STATIC_IO_BRANCH = cdn_config.get("branch", DEFAULT_STATIC_IO_BRANCH)

# Ensure IMAGE_SUB_DIR is not empty and is a valid relative path component
if not IMAGE_SUB_DIR or any(c in IMAGE_SUB_DIR for c in ['/', '\\', '..']):
    print(f"Warning: Invalid IMAGE_SUB_DIR '{IMAGE_SUB_DIR}'. Using default '{DEFAULT_IMAGE_SUB_DIR}'.")
    IMAGE_SUB_DIR = DEFAULT_IMAGE_SUB_DIR

# --- End Configuration ---

INDEX_HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shotput - Put your screenshots wherever you want</title>
    <style>
        body {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; /* Modern font stack */
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); /* Dark galaxy gradient */
            color: #e0e0e0; /* Light text color for contrast */
            overflow-x: hidden; /* Prevent horizontal scroll if gradient is too wide */
        }
        .container {
            background-color: rgba(20, 20, 40, 0.85); /* Semi-transparent dark slate blue */
            padding: 30px 40px;
            border-radius: 16px; /* Slightly more rounded */
            box-shadow: 0 0 25px rgba(102, 204, 255, 0.3), 0 0 10px rgba(255, 255, 255, 0.1) inset; /* Outer glow and subtle inner highlight */
            text-align: center;
            width: 90%;
            max-width: 550px; /* Slightly wider */
            border: 1px solid rgba(102, 204, 255, 0.2); /* Subtle border */
        }
        h1 {
            color: #ffffff;
            margin-bottom: 10px; /* Reduced margin to accommodate tagline */
            font-size: 2.8em; /* Slightly larger heading */
            text-shadow: 0 0 12px rgba(102, 204, 255, 0.6); /* Enhanced text glow */
        }
        .tagline {
            color: #c0c0c0; /* Light grey, slightly dimmer than main text */
            font-size: 1.1em;
            margin-bottom: 25px; /* Spacing below tagline */
            font-style: italic;
            text-shadow: 0 0 5px rgba(102, 204, 255, 0.3);
        }
        #pasteArea {
            width: 100%;
            box-sizing: border-box;
            min-height: 220px; /* Slightly taller */
            padding: 20px;
            border: 3px dashed rgba(102, 204, 255, 0.6); /* Dashed accent border */
            border-radius: 12px; /* More rounded */
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            margin-bottom: 25px;
            cursor: pointer;
            background-color: rgba(10, 10, 20, 0.5); /* Darker, semi-transparent background */
            transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
            overflow: hidden;
        }
        #pasteArea:hover, #pasteArea.dragover {
            background-color: rgba(30, 30, 50, 0.7);
            border-color: #66ccff; /* Brighter accent color on hover */
            box-shadow: 0 0 15px rgba(102, 204, 255, 0.5); /* Glow effect on hover */
        }
        #pasteArea p {
            color: #c0c0c0; /* Lighter paragraph text inside pasteArea */
            margin: 8px 0;
            font-size: 1.1em;
        }
        #pasteArea p small {
            font-size: 0.9em;
            color: #a0a0a0;
        }
        #preview {
            max-width: 100%;
            max-height: 180px; /* Keep preview size manageable */
            border-radius: 6px;
            object-fit: contain;
            margin-top: 10px; /* Add some space if image is shown */
            border: 1px solid rgba(102, 204, 255, 0.3); /* Subtle border for preview */
        }
        .result-container {
            margin-top: 25px;
            padding: 20px;
            background-color: rgba(30, 30, 50, 0.7); /* Consistent with pasteArea hover */
            border: 1px solid rgba(102, 204, 255, 0.3);
            border-radius: 10px;
            word-wrap: break-word;
            text-align: left;
            color: #e0e0e0; /* Ensure text is light */
        }
        .result-container p {
            margin: 5px 0;
            font-size: 0.95em;
        }
        .result-container strong {
            color: #ffffff; /* Brighter for strong text */
        }
        .result-container a {
            color: #66ccff; /* Accent color for links */
            text-decoration: none;
            font-weight: bold;
        }
        .result-container a:hover {
            text-decoration: underline;
            color: #99ddff; /* Lighter blue on hover */
        }
        #copyButton {
            background-color: #66ccff; /* Accent color */
            color: #0f0c29; /* Dark text for contrast on light blue button */
            border: none;
            padding: 12px 20px; /* Larger padding */
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            margin-top: 15px;
            transition: background-color 0.2s, transform 0.1s;
        }
        #copyButton:hover {
            background-color: #99ddff; /* Lighter accent on hover */
            transform: translateY(-1px); /* Subtle lift */
        }
        #copyButton.copied {
            background-color: #5cb85c; /* Success green - keep for clarity */
            color: white;
        }
        #copyButton.copied:hover {
            background-color: #4cae4c;
        }
        .status-message {
            margin-top: 20px;
            font-size: 0.95em;
        }
        .status-message.error {
            color: #ff6b6b; /* Brighter red for dark theme */
            font-weight: bold;
        }
        .status-message.success {
            color: #5cb85c; /* Success green - keep for clarity */
            font-weight: bold;
        }
        .loader {
            border: 4px solid rgba(200, 200, 200, 0.2); /* Lighter base for dark theme */
            border-top: 4px solid #66ccff; /* Accent color for spinner */
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
            display: none;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Shotput</h1>
        <p class="tagline">Put your screenshots wherever you want</p>
        <div id="pasteArea" tabindex="0">
            <p>Drop files or paste (Ctrl+V / Cmd+V)</p>
            <p><small>(Click to select file)</small></p>
            <img id="preview" src="#" alt="Image preview" style="display:none;"/>
        </div>
        <input type="file" id="fileInput" accept="image/*" style="display:none;">
        <div class="loader" id="loader"></div>
        <div id="result" class="result-container" style="display:none;">
            <p><strong>CDN Link:</strong> <a id="cdnLink" href="#" target="_blank"></a></p>
            <p><strong>Markdown:</strong> <code id="markdownLink"></code></p>
            <button id="copyButton">Copy Markdown</button>
        </div>
        <div id="statusMessage" class="status-message"></div>
    </div>

    <script src="script.js"></script>
</body>
</html>
"""

SCRIPT_JS_CONTENT = """
document.addEventListener('DOMContentLoaded', () => {
    const pasteArea = document.getElementById('pasteArea');
    const fileInput = document.getElementById('fileInput');
    const preview = document.getElementById('preview');
    const pasteAreaPrompts = pasteArea.querySelectorAll('p'); // Get the prompt paragraphs
    const resultDiv = document.getElementById('result');
    const cdnLink = document.getElementById('cdnLink');
    const markdownLink = document.getElementById('markdownLink');
    const copyButton = document.getElementById('copyButton');
    const statusMessage = document.getElementById('statusMessage');
    const loader = document.getElementById('loader');

    // Handle click on pasteArea to trigger file input
    pasteArea.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (event) => {
        const files = event.target.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    // Handle paste event
    document.addEventListener('paste', (event) => {
        const items = (event.clipboardData || event.originalEvent.clipboardData).items;
        for (let item of items) {
            if (item.kind === 'file' && item.type.startsWith('image/')) {
                const file = item.getAsFile();
                if (file) {
                    handleFile(file);
                    event.preventDefault(); // Prevent pasting as text/image in contentEditable
                    return;
                }
            }
        }
    });

    // Handle drag and drop
    pasteArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        pasteArea.classList.add('dragover');
    });

    pasteArea.addEventListener('dragleave', () => {
        pasteArea.classList.remove('dragover');
    });

    pasteArea.addEventListener('drop', (event) => {
        event.preventDefault();
        pasteArea.classList.remove('dragover');
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
    
    // Make pasteArea focusable for keyboard paste
    pasteArea.addEventListener('keydown', (event) => {
        if (event.key === 'v' && (event.ctrlKey || event.metaKey)) {
            // The 'paste' event listener on document will handle it
        }
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            showStatus('Please upload an image file.', true);
            return;
        }

        pasteAreaPrompts.forEach(p => p.style.display = 'none');
        preview.style.display = 'block';

        const reader = new FileReader();
        reader.onload = (e) => {
            preview.src = e.target.result;
        };
        reader.readAsDataURL(file);

        uploadFile(file);
    }

    async function uploadFile(file) {
        showLoader(true);
        showStatus(''); 
        resultDiv.style.display = 'none'; 

        const formData = new FormData();
        formData.append('image_blob', file);

        try {
            const response = await fetch('/upload_image/', {
                method: 'POST',
                body: formData,
            });

            showLoader(false);

            if (response.ok) {
                const data = await response.json();
                cdnLink.href = data.cdn_url;
                cdnLink.textContent = data.cdn_url;
                const markdown = `![${data.image_name}](${data.cdn_url})`;
                markdownLink.textContent = markdown;
                resultDiv.style.display = 'block';
                showStatus('Image uploaded successfully!', false);
                copyButton.textContent = 'Copy Markdown';
                copyButton.classList.remove('copied');
            } else {
                const errorData = await response.json();
                showStatus(`Error: ${errorData.detail || response.statusText}`, true);
                preview.style.display = 'none'; 
                preview.src = '#'; 
                pasteAreaPrompts.forEach(p => p.style.display = ''); 
            }
        } catch (error) {
            showLoader(false);
            showStatus(`Network error: ${error.message}`, true);
            preview.style.display = 'none'; 
            preview.src = '#'; 
            pasteAreaPrompts.forEach(p => p.style.display = ''); 
        }
    }

    copyButton.addEventListener('click', () => {
        navigator.clipboard.writeText(markdownLink.textContent)
            .then(() => {
                copyButton.textContent = 'Copied!';
                copyButton.classList.add('copied');
                setTimeout(() => {
                    copyButton.textContent = 'Copy Markdown';
                    copyButton.classList.remove('copied');
                }, 2000);
            })
            .catch(err => {
                showStatus('Failed to copy markdown.', true);
                console.error('Failed to copy: ', err);
            });
    });

    function showStatus(message, isError = false) {
        statusMessage.textContent = message;
        statusMessage.className = 'status-message'; 
        if (message) {
            statusMessage.classList.add(isError ? 'error' : 'success');
        }
    }

    function showLoader(show) {
        loader.style.display = show ? 'block' : 'none';
    }
});
"""

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    is_default_path = str(IMAGES_REPO_PATH) == DEFAULT_IMAGES_REPO_PATH_STR
    is_default_user = STATIC_IO_USER == DEFAULT_STATIC_IO_USER
    
    if is_default_path or is_default_user:
        print("--- SHOTPUT CONFIGURATION WARNING ---")
        if is_default_path:
            print(f"WARNING: IMAGES_REPO_PATH is using the default value: {IMAGES_REPO_PATH}")
        if is_default_user:
            print(f"WARNING: STATIC_IO_USER is using the default value: {STATIC_IO_USER}")
        print("Please ensure these are correctly configured in 'config.toml'.")
        print("--- END SHOTPUT CONFIGURATION WARNING ---")

    resolved_image_save_dir = IMAGES_REPO_PATH / IMAGE_SUB_DIR
    try:
        resolved_image_save_dir.mkdir(parents=True, exist_ok=True)
        print(f"Image save directory ensured: {resolved_image_save_dir}")
    except Exception as e:
        print(f"CRITICAL ERROR: Could not create image save directory {resolved_image_save_dir}. "
              f"Please check permissions and path configuration. Error: {e}")
        # Consider raising an error to halt startup if the directory is essential
        # raise RuntimeError(f"Could not create image save directory: {e}")

@app.get("/", response_class=HTMLResponse)
async def get_index_html():
    return INDEX_HTML_CONTENT

@app.get("/script.js", response_class=Response)
async def get_script_js():
    return Response(content=SCRIPT_JS_CONTENT, media_type="application/javascript")

@app.post("/upload_image/")
async def upload_image(image_blob: UploadFile = File(...)):
    try:
        # Basic check if using default placeholder values that might indicate misconfiguration
        if str(IMAGES_REPO_PATH) == DEFAULT_IMAGES_REPO_PATH_STR and STATIC_IO_USER == DEFAULT_STATIC_IO_USER:
             print("INFO: Processing upload with default repository path and user. Ensure this is intended.")

        if not image_blob.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        content_type_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        file_extension = content_type_map.get(image_blob.content_type.lower(), ".png")
        
        image_name = f"{timestamp}_{unique_id}{file_extension}"
        
        current_image_save_dir = IMAGES_REPO_PATH / IMAGE_SUB_DIR
        image_path = current_image_save_dir / image_name

        contents = await image_blob.read()
        
        try:
            img = Image.open(io.BytesIO(contents))
            if img.format and img.format.upper() in ["HEIC", "HEIF"]:
                image_name = f"{timestamp}_{unique_id}.png"
                image_path = current_image_save_dir / image_name
                img.save(image_path, "PNG")
            else:
                with open(image_path, "wb") as f:
                    f.write(contents)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid or unsupported image file: {str(e)}")

        commit_message = f"Add image {image_name} via Shotput"
        success, message = commit_and_push_image(IMAGES_REPO_PATH, image_path, commit_message, GIT_AUTO_PUSH)
        
        if not success:
            image_path.unlink(missing_ok=True) 
            raise HTTPException(status_code=500, detail=f"Failed to commit image: {message}")

        cdn_url = f"https://cdn.statically.io/gh/{STATIC_IO_USER}/{STATIC_IO_REPO}/{STATIC_IO_BRANCH}/{IMAGE_SUB_DIR}/{image_name}"
        
        return JSONResponse(content={"cdn_url": cdn_url, "image_name": image_name})

    except HTTPException as e:
        raise e # Re-raise known HTTP exceptions
    except Exception as e:
        print(f"An unexpected error occurred during upload: {e}") # Log for server-side debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An internal server error occurred during image processing.")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    print("--- Shotput Application Runner ---")
    print("Attempting to start server on http://0.0.0.0:8000")
    print(f"Using image repository: {IMAGES_REPO_PATH.resolve()}")
    print(f"Image subdirectory: {IMAGE_SUB_DIR}")
    print(f"Statically.io CDN: User='{STATIC_IO_USER}', Repo='{STATIC_IO_REPO}', Branch='{STATIC_IO_BRANCH}'")
    print(f"Git auto-push: {'Enabled' if GIT_AUTO_PUSH else 'Disabled'}")
    print(f"Config loaded from: {CONFIG_FILE_PATH.resolve() if CONFIG_FILE_PATH.exists() else 'Defaults (config file not found or error)'}")
    if not CONFIG_FILE_PATH.exists() or STATIC_IO_USER == DEFAULT_STATIC_IO_USER or STATIC_IO_REPO == DEFAULT_STATIC_IO_REPO:
        print("\nIMPORTANT: Review 'config.toml'. Update 'static_cdn.user' and 'static_cdn.repo' with your actual GitHub username and image repository name.")
    
    is_default_path_main = str(IMAGES_REPO_PATH) == DEFAULT_IMAGES_REPO_PATH_STR
    is_default_user_main = STATIC_IO_USER == DEFAULT_STATIC_IO_USER

    if is_default_path_main or is_default_user_main:
        print("\n--- CONFIGURATION NOTICE (from main execution block) ---")
        if is_default_path_main:
            print(f"WARNING: IMAGES_REPO_PATH is set to its default value: {IMAGES_REPO_PATH}")
        if is_default_user_main:
            print(f"WARNING: STATIC_IO_USER is set to its default value: {STATIC_IO_USER}")
        print("If these are not your intended settings, please stop the server (Ctrl+C),")
        print(f"edit the configuration variables at the top of {Path(__file__).resolve()}, and restart.")
        print("--- END CONFIGURATION NOTICE ---\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)