FROM twobombs/deploy-nvidia-docker

RUN git clone --recursive http://git.tiker.net/trees/pycuda.git

RUN add-apt-repository universe
RUN apt-get update
RUN apt-get install libboost-all-dev python-pycuda python-pip 

RUN pip install numpy scipy

EXPOSE 5900 6080