import subprocess

def convert_480p(source):
    target = source + '_480p.mp4'
    cmd = 'ffmpeg -i "{source}" -s hd480 -c:v libx264 -crf 23 -c:a aac -strict -2 "{target}"'.format(source=source, target=target)
    subprocess.run(cmd, shell=True, check=True)
    return target