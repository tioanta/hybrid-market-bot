import os
from instagrapi import Client

def upload_image(image_path, caption):
    print("--- UPLOAD INSTAGRAM ---")
    username = os.environ.get("IG_USERNAME")
    password = os.environ.get("IG_PASSWORD")
    session_id = os.environ.get("IG_SESSION_ID")
    
    cl = Client()
    cl.delay_range = [1, 3]

    try:
        if session_id:
            print("Login via Session ID...")
            cl.login_by_sessionid(session_id)
        else:
            print("Login via User/Pass...")
            cl.login(username, password)
        
        try:
            cl.account_info()
            print("✅ Login Valid.")
        except Exception as e:
            print(f"❌ Session Invalid: {e}")
            raise e

        cl.photo_upload(path=image_path, caption=caption)
        print("🎉 Upload Berhasil!")
        
    except Exception as e:
        print(f"!! Gagal Upload: {e}")
