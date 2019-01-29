FROM twobombs/deploy-nvidia-docker

RUN apt-get update&&apt-get install -y git software-properties-common python-software-properties python-setuptools python3-setuptools python-migrate && apt-get clean all

RUN git clone --recursive http://git.tiker.net/trees/pycuda.git
RUN git clone --recursive https://github.com/stevenrobertson/cuburn.git

RUN add-apt-repository universe && apt-get update && export DEBIAN_FRONTEND=noninteractive && apt-get upgrade && apt-get install -y libboost-all-dev python-pycuda python-pip && apt-get clean all

RUN pip install numpy scipy
