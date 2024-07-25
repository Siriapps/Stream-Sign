import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
from flask import Flask, request, send_file, render_template, redirect
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
from openai import OpenAI
from werkzeug.utils import secure_filename
from google.cloud import speech, storage
import io
from flask_dropzone import Dropzone


app = Flask(__name__)
app.config.update(
    # DROPZONE_REDIRECT_VIEW='process'
    DROPZONE_MAX_FILE_SIZE=100,
    # DROPZONE_IN_FORM=True,
    # DROPZONE_UPLOAD_ON_CLICK=True,
    # DROPZONE_UPLOAD_ACTION='process',  # URL or endpoint
    # DROPZONE_UPLOAD_BTN_ID='submit'
)

dropzone = Dropzone(app)
client = OpenAI(api_key="sk-proj-mHYAUxNB8ehe2Vs86xhsT3BlbkFJXAUrAqco1AQc3jCyb0l4")
app.config["UPLOAD_FOLDER"] = "uploads/"
VIDEO_DIR = r"C:\Users\siria\OneDrive\Documents\code\VideoToSignApp\assets\Videos"

def find_video(word):
    for extension in ['.mp4', '.mkv']:
        video_path = os.path.normpath(os.path.join(VIDEO_DIR, word + extension))
        print("This is video path 1:", video_path)
        if os.path.exists(video_path):
            return video_path
    return None

def map_sentence_to_videos(lst):
    words = lst[:10]
    video_clips = []

    for word in words:
        video_path = find_video(word)
        print("This is video path 2:", video_path)

        if video_path:
            video_clips.append(VideoFileClip(video_path))
        else:
            for char in word:
                char_video_path = find_video(char)
                print("This is video path 3:", char_video_path)
                if char_video_path:
                    video_clips.append(VideoFileClip(char_video_path))
                else:
                    print(f"No video found for the character: {char}")
                    # return None
    print ("This is videoClips123: -", video_clips)
    return video_clips

def text_to_sl(text):
    #tokenizing the sentence
    text.lower()
    #tokenizing the sentence
    words = word_tokenize(text)

    tagged = nltk.pos_tag(words)
    tense = {}
    tense["future"] = len([word for word in tagged if word[1] == "MD"])
    tense["present"] = len([word for word in tagged if word[1] in ["VBP", "VBZ","VBG"]])
    tense["past"] = len([word for word in tagged if word[1] in ["VBD", "VBN"]])
    tense["present_continuous"] = len([word for word in tagged if word[1] in ["VBG"]])



    #stopwords that will be removed
    stop_words = set(["mightn't", 're', 'wasn', 'wouldn', 'be', 'has', 'that', 'does', 'shouldn', 'do', "you've",'off', 'for', "didn't", 'm', 'ain', 'haven', "weren't", 'are', "she's", "wasn't", 'its', "haven't", "wouldn't", 'don', 'weren', 's', "you'd", "don't", 'doesn', "hadn't", 'is', 'was', "that'll", "should've", 'a', 'then', 'the', 'mustn', 'i', 'nor', 'as', "it's", "needn't", 'd', 'am', 'have',  'hasn', 'o', "aren't", "you'll", "couldn't", "you're", "mustn't", 'didn', "doesn't", 'll', 'an', 'hadn', 'whom', 'y', "hasn't", 'itself', 'couldn', 'needn', "shan't", 'isn', 'been', 'such', 'shan', "shouldn't", 'aren', 'being', 'were', 'did', 'ma', 't', 'having', 'mightn', 've', "isn't", "won't"])



    #removing stopwords and applying lemmatizing nlp process to words
    lr = WordNetLemmatizer()
    filtered_text = []
    for w,p in zip(words,tagged):
        if w not in stop_words:
            if p[1]=='VBG' or p[1]=='VBD' or p[1]=='VBZ' or p[1]=='VBN' or p[1]=='NN':
                filtered_text.append(lr.lemmatize(w,pos='v'))
            elif p[1]=='JJ' or p[1]=='JJR' or p[1]=='JJS'or p[1]=='RBR' or p[1]=='RBS':
                filtered_text.append(lr.lemmatize(w,pos='a'))

            else:
                filtered_text.append(lr.lemmatize(w))



    #adding the specific word to specify tense
    words = filtered_text
    temp=[]
    for w in words:
        if w=='I':
            temp.append('Me')
        else:
            temp.append(w)
    words = temp
    probable_tense = max(tense,key=tense.get)

    if probable_tense == "past" and tense["past"]>=1:
        temp = ["Before"]
        temp = temp + words
        words = temp
    elif probable_tense == "future" and tense["future"]>=1:
        if "Will" not in words:
                temp = ["Will"]
                temp = temp + words
                words = temp
        else:
            pass
    elif probable_tense == "present":
        if tense["present_continuous"]>=1:
            temp = ["Now"]
            temp = temp + words
            words = temp

    video_clips = map_sentence_to_videos(words)
    print(video_clips)

    if video_clips:
        final_clip = concatenate_videoclips(video_clips, method='compose')
        output_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),"static","output_video.mp4")
        
        final_clip.write_videofile(output_path)

        return "/static/output_video.mp4"
    else:
        return "Clips not found for the words or chars", 400

@app.route('/', methods=["GET","POST"])
def index():
    return render_template('index.html')

@app.route('/process', methods=["GET","POST"])
def process():
    if request.method =="POST":
        print("File recieved")
    
        if "file" not in request.files:
            return redirect("index.html")
        file = request.files["file"]
        if file.filename == "":
            return redirect("index.html")
        print(file.filename)
        if file:
            destination = os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config["UPLOAD_FOLDER"],secure_filename(file.filename))
            file.save(destination)
            video = VideoFileClip(destination)
            audio = video.audio
            audio.write_audiofile("output_audio.mp3")
            client = speech.SpeechClient()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="C:/Users/siria/AppData/Roaming/gcloud/application_default_credentials.json"
            os.environ["GCLOUD_PROJECT"] = "my-new-project-310201"
            storage_client = storage.Client()

            buckets = list(storage_client.list_buckets())

            bucket = storage_client.get_bucket("myaudio_files") # your bucket name

            blob = bucket.blob('audios/FileConvert')
            blob.upload_from_filename("output_audio.mp3")
            link = 'gs://' + blob.id[:-(len(str(blob.generation)) + 1)]
            print(blob.public_url)

            audio = speech.RecognitionAudio(uri=link)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                sample_rate_hertz=16000,
                language_code="en-US",
            )
            operation = client.long_running_recognize(config=config, audio=audio)

            print("Waiting for operation to complete...")
            response = operation.result(timeout=90)

            transcript_builder = []
            # Each result is for a consecutive portion of the audio. Iterate through
            # them to get the transcripts for the entire audio file.
            for result in response.results:
                # The first alternative is the most likely one for this portion.
                transcript_builder.append(f"{result.alternatives[0].transcript}")
                # transcript_builder.append(f"\nConfidence: {result.alternatives[0].confidence}")
            

            transcript = "".join(transcript_builder)
            print(transcript)

            outVid = text_to_sl(transcript)
            # outVid = "/static/output_video.mp4" 
            print("This is 1:- ", outVid)
            return render_template("index.html", output=outVid, transcript=transcript) # unable to see the video
    
    else:
        return render_template("index.html") 

@app.route('/animation_view', methods=['POST'])
def animation_view():
    if request.method == 'POST':
        text = request.form['sentence']
        outVid = text_to_sl(text)
        print("This is 2:- ", outVid)
        return render_template('index.html', output=outVid, transcript=text)
    


if __name__ == '__main__':
    app.run(debug=True)