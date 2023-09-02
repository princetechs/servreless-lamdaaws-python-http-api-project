import boto3
import instaloader
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import json
import time  # Add this import for timestamp generation

s3 = boto3.client(
    's3',
    aws_access_key_id='change_it',
    aws_secret_access_key='change_it'
)

def get_slider_images(post_url):
    L = instaloader.Instaloader()

    try:
        post = instaloader.Post.from_shortcode(L.context, post_url.split("/")[-2])

        image_urls = []
        for slide in post.get_sidecar_nodes():
            if slide.is_video:
                image_urls.append(slide.video_url)
            else:
                image_urls.append(slide.display_url)

        return image_urls
    except instaloader.exceptions.NotFoundException:
        return None

def create_pdf(image_urls, pdf_file_name):
    c = canvas.Canvas(pdf_file_name, pagesize=letter)

    page_width, page_height = letter
    margin = 50
    image_width = page_width - 2 * margin
    image_height = image_width  # Maintain aspect ratio

    for image_url in image_urls:
        img = ImageReader(image_url)
        c.drawImage(img, margin, margin, width=image_width, height=image_height)
        c.showPage()

    c.save()

def lambda_handler(event, context):
    post_url = "https://www.instagram.com/p/CuMdH7UsssG/?utm_source=ig_web_copy_link&igshid=MzRlODBiNWFlZA=="

    image_urls = get_slider_images(post_url)
    if image_urls:
        # Generate a unique PDF file name based on the current timestamp
        timestamp = int(time.time())
        pdf_file_name = f"/tmp/slider_images_{timestamp}.pdf"
        create_pdf(image_urls, pdf_file_name)

        s3.upload_file(pdf_file_name, 'change_it', pdf_file_name)

        s3_url = f"https://insta-to-pdf-devsan.s3.amazonaws.com/{pdf_file_name}"
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "PDF created and uploaded successfully", "pdf_url": s3_url}),
        }
    else:
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Image URLs not found for the post."}),
        }
