from django.shortcuts import render

def index(request):
    return render(request, "home/index.html")

def self(request):
    return render(request, "home/self.html")

def SE(request):
    return render(request, "home/SE.html")

def CS(request):
    return render(request, "home/CS.html")

def rpser(request):
    return render(request, "RPSer/rpser.html")
