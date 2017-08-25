FROM twobombs/deploy-nvidia-docker

RUN git clone --recursive http://git.tiker.net/trees/pycuda.git
RUN git clone --recursive https://github.com/twobombs/cuburn.git

RUN add-apt-repository universe
RUN apt-get update
RUN apt-get install -y libboost-all-dev python-pycuda python-pip 

RUN pip install numpy scipy

EXPOSE 5900 6080
