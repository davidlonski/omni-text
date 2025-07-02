import streamlit as st
import io
from PIL import Image
import os
from dotenv import load_dotenv
import json
import base64
import sys

# Add UserCentral to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'UserCentral'))

# Import the modules from our package
from file_parser import parse_powerpoint, replace_images_with_videos
from utils import configure_gemini, describe_image, create_static_video, generate_audio

# Import user management
from UserCentral.user_controller import validate_user, has_permission, get_user_permissions, get_all_users, create_user, delete_user, get_users_by_role
from UserCentral.User import User

# --- Page Configuration ---
st.set_page_config(
    page_title="PowerPoint RAG Quizzer",
    page_icon="🧠",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Configure Gemini model
configure_gemini()

# --- Application Title ---
st.title("🧠 PowerPoint RAG Quizzer")
st.markdown("Upload a PowerPoint, describe its images, and test your knowledge with an AI-powered quiz.")

# --- Session State Initialization ---
def init_session_state():
    """Initialize session state variables."""
    if 'app_stage' not in st.session_state:
        st.session_state.app_stage = 'login'
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = []
    if 'images_to_describe' not in st.session_state:
        st.session_state.images_to_describe = []
    if 'current_image_index' not in st.session_state:
        st.session_state.current_image_index = 0
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'user_permissions' not in st.session_state:
        st.session_state.user_permissions = {}

init_session_state()

# --- Helper Functions ---
def reset_app():
    """Resets the application to its initial state."""
    st.cache_data.clear()
    st.cache_resource.clear()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def prepare_data_for_json(data_list):
    """Convert binary data to base64 strings for JSON serialization."""
    json_safe_data = []
    for item in data_list:
        json_item = item.copy()
        if item['type'] == 'image' and isinstance(item['image_bytes'], bytes):
            # Convert binary image data to base64 string
            json_item['image_bytes'] = base64.b64encode(item['image_bytes']).decode('utf-8')
        json_safe_data.append(json_item)
    return json_safe_data

def login_user(email: str, password: str):
    """Authenticate user and set session state."""
    user = validate_user(email, password)
    if user:
        st.session_state.current_user = user
        st.session_state.user_permissions = get_user_permissions(user)
        if user.role == 'teacher':
            st.session_state.app_stage = 'teacher_dashboard'
        elif user.role == 'student':
            st.session_state.app_stage = 'student_dashboard'
        else:
            st.session_state.app_stage = 'student_dashboard'
        return True
    return False

def logout_user():
    """Logout current user."""
    st.session_state.current_user = None
    st.session_state.user_permissions = {}
    st.session_state.app_stage = 'login'
    st.rerun()

# --- Sidebar ---
with st.sidebar:
    st.header("Configuration & Control")
    
    # Show user info if logged in
    if st.session_state.current_user:
        st.success(f"Logged in as: {st.session_state.current_user.name}")
        st.info(f"Role: {st.session_state.current_user.role}")
        
        # Dashboard button
        if st.button("🏠 Dashboard", use_container_width=True):
            if st.session_state.current_user.role == 'teacher':
                st.session_state.app_stage = 'teacher_dashboard'
            elif st.session_state.current_user.role == 'student':
                st.session_state.app_stage = 'student_dashboard'
            else:
                st.session_state.app_stage = 'student_dashboard'
            st.rerun()
        
        # Show permissions
        if st.session_state.user_permissions:
            st.subheader("Your Permissions:")
            for permission, has_access in st.session_state.user_permissions.items():
                status = "✅" if has_access else "❌"
                st.write(f"{status} {permission.replace('_', ' ').title()}")
        
        # Admin/Teacher user management
        if has_permission(st.session_state.current_user, 'can_manage_users'):
            st.subheader("User Management")
            if st.button("Manage Users"):
                st.session_state.app_stage = 'user_management'
                st.rerun()
        
        if st.button("Logout"):
            logout_user()
    
    if st.button("Start Over"):
        reset_app()

# --- Main Application Flow ---

# STAGE 0: Login
if st.session_state.app_stage == 'login':
    st.header("🔐 Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if login_user(email, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password")
    
    # Show default credentials
    with st.expander("Default Login Credentials"):
        st.write("**Admin:** admin@gmail.com / admin")
        st.write("**Teacher:** teacher@gmail.com / teacher")
        st.write("**Student:** student@gmail.com / student")

# STAGE 1: User Management (Admin/Teacher only)
elif st.session_state.app_stage == 'user_management':
    if not has_permission(st.session_state.current_user, 'can_manage_users'):
        st.error("You don't have permission to access user management.")
        st.session_state.app_stage = 'upload'
        st.rerun()
    
    st.header("👥 User Management")
    
    # Create new user
    with st.expander("Create New User"):
        with st.form("create_user_form"):
            new_name = st.text_input("Name")
            new_age = st.number_input("Age", min_value=0, max_value=120, value=20)
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["student", "teacher", "admin"])
            
            if st.form_submit_button("Create User"):
                try:
                    new_user = User(
                        name=new_name,
                        age=new_age,
                        email=new_email,
                        password=new_password,
                        role=new_role
                    )
                    if create_user(new_user):
                        st.success("User created successfully!")
                    else:
                        st.error("Email already exists!")
                except Exception as e:
                    st.error(f"Error creating user: {str(e)}")
    
    # View all users
    st.subheader("All Users")
    all_users = get_all_users()
    
    for user in all_users:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(f"**{user.name}** ({user.email})")
        with col2:
            st.write(f"Role: {user.role}")
        with col3:
            st.write(f"Age: {user.age}")
        with col4:
            if st.button(f"Delete {user.name}", key=f"delete_{user.id}"):
                if delete_user(user.id):
                    st.success("User deleted!")
                    st.rerun()
                else:
                    st.error("Failed to delete user")


# STAGE 2: File Upload
elif st.session_state.app_stage == 'upload':
    if not has_permission(st.session_state.current_user, 'can_upload_files'):
        st.error("You don't have permission to upload files.")
        st.rerun()
    
    st.header("1. Upload Your PowerPoint")
    uploaded_file = st.file_uploader("Choose a .pptx file", type="pptx")
    if uploaded_file:
        with st.spinner("Parsing your PowerPoint..."):
            file_in_memory = io.BytesIO(uploaded_file.getvalue())
            st.session_state.extracted_data = parse_powerpoint(file_in_memory)
            st.session_state.images_to_describe = [
                item for item in st.session_state.extracted_data if item['type'] == 'image'
            ]

            # Convert data for JSON serialization
            extracted_data_json = json.dumps(prepare_data_for_json(st.session_state.extracted_data), indent=2)
            # write json to a file, if content exists, overwrite it
            if os.path.exists('extracted_data_stage1.json'):
                os.remove('extracted_data_stage1.json')
            with open('extracted_data_stage1.json', 'w') as f:
                f.write(extracted_data_json)

            st.session_state.current_image_index = 0
            st.success(f"Parsed! Found {len(st.session_state.extracted_data) - len(st.session_state.images_to_describe)} text blocks and {len(st.session_state.images_to_describe)} images.")
            
            if st.session_state.images_to_describe:
                st.session_state.app_stage = 'describe_images'
            else:
                st.session_state.app_stage = 'initialize_rag'
            st.rerun()

# STAGE 3: Describe Images
elif st.session_state.app_stage == 'describe_images':
    if not has_permission(st.session_state.current_user, 'can_describe_images'):
        st.error("You don't have permission to describe images.")
        st.rerun()
    
    st.header("2. Describe the Images")
    total = len(st.session_state.images_to_describe)
    idx = st.session_state.current_image_index

    if idx < total:
        img_item = st.session_state.images_to_describe[idx]
        st.progress((idx + 1) / total)
        st.write(f"**Image {idx + 1} of {total}** (from Slide {img_item['slide_number']})")
        st.image(Image.open(io.BytesIO(img_item['image_bytes'])), use_container_width=True)

        description = st.text_area("What is important about this image?", key=f"desc_{img_item['id']}", value=describe_image(img_item['image_bytes'], img_item['extension']))
        
        if st.button("Submit Description", key=f"submit_{idx}"):
            if description:
                # Add description directly to the image object
                img_item['description'] = description
                st.session_state.current_image_index += 1
                st.rerun()
            else:
                st.warning("Please provide a description.")
    else:
        st.success("All images described!")
        st.session_state.app_stage = 'initialize_rag'
        st.rerun()



# STAGE 4: Add Audio to PPTX
elif st.session_state.app_stage == 'add_audio_to_pptx':
    
    # Initialize step tracking
    if 'audio_pptx_step' not in st.session_state:
        st.session_state.audio_pptx_step = 1
    
    st.header("🎥 Add Audio to PowerPoint")
    
    # Progress indicator
    steps = ["Upload PPTX", "Describe Images", "Generate Audio/Video", "Download"]
    current_step = st.session_state.audio_pptx_step
    
    # Create progress bar
    progress_cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with progress_cols[i]:
            if i + 1 < current_step:
                st.success(f"✅ {step}")
            elif i + 1 == current_step:
                st.info(f"🔄 {step}")
            else:
                st.write(f"⏳ {step}")
    
    st.markdown("---")
    
    # STEP 1: Upload PPTX
    if st.session_state.audio_pptx_step == 1:
        st.subheader("Step 1: Upload PowerPoint")
        uploaded_file = st.file_uploader("Choose a .pptx file", type="pptx", key="audio_pptx_upload")
        
        if uploaded_file:
            with st.spinner("Parsing your PowerPoint..."):
                file_in_memory = io.BytesIO(uploaded_file.getvalue())
                st.session_state.extracted_data = parse_powerpoint(file_in_memory)
                st.session_state.images_to_describe = [
                    item for item in st.session_state.extracted_data if item['type'] == 'image'
                ]
                st.session_state.uploaded_file = uploaded_file
            
            st.success(f"✅ PowerPoint parsed! Found {len(st.session_state.images_to_describe)} images.")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Next: Describe Images", use_container_width=True, type="primary"):
                    st.session_state.audio_pptx_step = 2
                    st.rerun()

    # STEP 2: Describe Images
    elif st.session_state.audio_pptx_step == 2:
        st.subheader("Step 2: Describe Images")
        total = len(st.session_state.images_to_describe)
        
        if total > 0:
            st.write(f"**Found {total} images to describe**")
            
            # Create a scrollable container for all images
            with st.container():
                # Add some CSS to make the container scrollable
                st.markdown("""
                    <style>
                    .scrollable-container {
                        max-height: 600px;
                        overflow-y: auto;
                        border: 1px solid #ddd;
                        padding: 10px;
                        border-radius: 5px;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                
                # Create the scrollable container
                with st.container():
                    st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
                    
                    for idx, img_item in enumerate(st.session_state.images_to_describe):
                        st.markdown(f"### Image {idx + 1} of {total} (Slide {img_item['slide_number']})")
                        
                        # Display image
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.image(Image.open(io.BytesIO(img_item['image_bytes'])), use_container_width=True)
                        
                        with col2:
                            # Generate initial description if not already present
                            if 'description' not in img_item:
                                image_description = describe_image(img_item['image_bytes'], img_item['extension'])
                                img_item['description'] = image_description
                            
                            # Text area for description
                            description = st.text_area(
                                "What is important about this image?", 
                                key=f"desc_{img_item['id']}", 
                                value=img_item.get('description', ''),
                                height=150
                            )
                            
                            # Update the description in the session state
                            img_item['description'] = description
                            
                            # Audio playback section
                            st.markdown("**Audio Preview:**")
                            
                            # Generate audio if not already present
                            if 'audio_bytes' not in img_item and description:
                                audio_bytes = generate_audio(description)
                                if audio_bytes:
                                    img_item['audio_bytes'] = audio_bytes
                            
                            # Display audio player if audio exists
                            if 'audio_bytes' in img_item and img_item['audio_bytes']:
                                st.audio(img_item['audio_bytes'], format='audio/wav')
                            else:
                                st.info("Audio will be generated when you save descriptions")
                            
                            # Regenerate audio button
                            if st.button(f"🔄 Regenerate Audio", key=f"regen_audio_{img_item['id']}"):
                                if description:
                                    with st.spinner("Generating audio..."):
                                        audio_bytes = generate_audio(description)
                                        if audio_bytes:
                                            img_item['audio_bytes'] = audio_bytes
                                            st.success("Audio regenerated!")
                                            st.rerun()
                                else:
                                    st.warning("Please add a description first")
                        
                        st.markdown("---")  # Separator between images
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("← Back to Upload", use_container_width=True):
                    st.session_state.audio_pptx_step = 1
                    st.rerun()
            
            with col3:
                if st.button("Next: Generate Audio/Video →", use_container_width=True, type="primary"):
                    st.session_state.audio_pptx_step = 3
                    st.rerun()
        else:
            st.warning("No images found in the PowerPoint.")
            if st.button("Continue to Next Stage"):
                st.session_state.audio_pptx_step = 3
                st.rerun()

    # STEP 3: Generate Audio/Video
    elif st.session_state.audio_pptx_step == 3:
        st.subheader("Step 3: Generate Audio/Video")
        
        if st.button("🎬 Generate Audio and Video for All Images", use_container_width=True, type="primary"):
            # Process all images with descriptions
            with st.spinner("Processing images and generating audio/video..."):
                total = len(st.session_state.images_to_describe)
                for idx, img_item in enumerate(st.session_state.images_to_describe):
                    if img_item.get('description'):
                        # Generate audio and video for each image
                        audio_bytes = img_item.get('audio_bytes')
                        if not audio_bytes:
                            audio_bytes = generate_audio(img_item['description'])
                            img_item['audio_bytes'] = audio_bytes
                        
                        video_bytes = create_static_video(img_item['image_bytes'], audio_bytes)
                        
                        # Store the generated content
                        img_item['video_bytes'] = video_bytes
                        
                        # Update progress
                        st.progress((idx + 1) / total)
            
            st.success("✅ All audio and video generated successfully!")
            st.session_state.audio_pptx_step = 4
            st.rerun()
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back to Describe Images", use_container_width=True):
                st.session_state.audio_pptx_step = 2
                st.rerun()

    # STEP 4: Display JSON
    elif st.session_state.audio_pptx_step == 4:
        st.subheader("Step 4: Download Enhanced PowerPoint")
        # make sure the [image][content], [image][audio], [image][video] is less than 100 characters

        # make sure the [image][content], [image][audio], [image][video] is less than 100 characters
        for item in st.session_state.extracted_data:
            if item['type'] == 'image':
                item['image_bytes'] = item['image_bytes'][:100]
                item['audio_bytes'] = item['audio_bytes'][:100]
                item['video_bytes'] = item['video_bytes'][:100]

        st.json(st.session_state.extracted_data)
        




# STAGE 4: Initialize RAG
elif st.session_state.app_stage == 'initialize_rag':
    with st.spinner("Building the knowledge base... This may take a moment."):

        # Convert data for JSON serialization
        extracted_data_json = json.dumps(prepare_data_for_json(st.session_state.extracted_data), indent=2)
        # write json to a file, if content exists, overwrite it
        if os.path.exists('extracted_data_stage2.json'):
            os.remove('extracted_data_stage2.json')
        with open('extracted_data_stage2.json', 'w') as f:
            f.write(extracted_data_json)
        
        # Display JSON with truncated values (only for users with permission)
        if has_permission(st.session_state.current_user, 'can_view_all_data'):
            extracted_data_json = json.loads(extracted_data_json)
            for item in extracted_data_json:
                for key, value in item.items():
                    if isinstance(value, str):
                        item[key] = value[:100]
            st.json(extracted_data_json)
        else:
            st.info("Data processing complete. Contact an administrator to view detailed data.")



# STAGE 5: Teacher Dashboard
elif st.session_state.app_stage == 'teacher_dashboard':
    st.header("3. Teacher Dashboard")
    st.write("Welcome to the Teacher Dashboard. Select an action below:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 Upload PowerPoint", use_container_width=True):
            st.session_state.app_stage = 'upload'
            st.rerun()
        
        if st.button("🖼️ Describe Images", use_container_width=True):
            if st.session_state.extracted_data:
                st.session_state.app_stage = 'describe_images'
                st.rerun()
            else:
                st.warning("Please upload a PowerPoint first.")
        
        if st.button("🧠 Take Quiz", use_container_width=True):
            if st.session_state.extracted_data:
                st.session_state.app_stage = 'initialize_rag'
                st.rerun()
            else:
                st.warning("Please upload a PowerPoint first.")
    
    with col2:
        if st.button("👥 Manage Users", use_container_width=True):
            st.session_state.app_stage = 'user_management'
            st.rerun()
        
        if st.button("📊 View All Data", use_container_width=True):
            if st.session_state.extracted_data:
                st.session_state.app_stage = 'initialize_rag'
                st.rerun()
            else:
                st.warning("Please upload a PowerPoint first.")
        
        if st.button("⚙️ Configure App", use_container_width=True):
            st.info("Configuration options will be available here.")

        if st.button("🎥 Add Audio to PPTX", use_container_width=True):
            st.session_state.app_stage = 'add_audio_to_pptx'
            st.rerun()

# STAGE 6: Student Dashboard
elif st.session_state.app_stage == 'student_dashboard':
    st.header("4. Student Dashboard")
    st.write("Welcome to the Student Dashboard. Select an action below:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 Upload PowerPoint", use_container_width=True):
            st.session_state.app_stage = 'upload'
            st.rerun()
        
        if st.button("🖼️ Describe Images", use_container_width=True):
            if st.session_state.extracted_data:
                st.session_state.app_stage = 'describe_images'
                st.rerun()
            else:
                st.warning("Please upload a PowerPoint first.")
    
    with col2:
        if st.button("🧠 Take Quiz", use_container_width=True):
            if st.session_state.extracted_data:
                st.session_state.app_stage = 'initialize_rag'
                st.rerun()
            else:
                st.warning("Please upload a PowerPoint first.")
        
        if st.button("📊 View My Data", use_container_width=True):
            if st.session_state.extracted_data:
                st.session_state.app_stage = 'initialize_rag'
                st.rerun()
            else:
                st.warning("Please upload a PowerPoint first.")
