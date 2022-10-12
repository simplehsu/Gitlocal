ARG UBUNTU_VERSION=20.04
FROM ubuntu:$UBUNTU_VERSION

# https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
# all apt-get needs to be part of the same RUN command
RUN apt-get update --fix-missing && \
    apt-get dist-upgrade -y && \
    apt-get install -y \
    sudo

# for apt to be noninteractive
RUN DEBIAN_FRONTEND=noninteractive TZ=Asia/Taipei apt-get -y install tzdata

# Install software that will use the HSM. For this case, that’s
RUN sudo apt-get update && sudo apt-get dist-upgrade -y
RUN sudo apt-get install -y openssl
RUN sudo apt-get install -y pkgconf libssl-dev
RUN sudo apt-get install -y pkgconf libengine-pkcs11-openssl
RUN sudo apt-get install -y pkgconf opensc-pkcs11

# INSTALL YUBIHSM
RUN sudo apt-get update && sudo apt-get dist-upgrade -y
RUN sudo apt-get install -y \
    build-essential \
    git \
    libpcsclite1 \
    curl \
    usbutils \
    libusb-1.0-0-dev \
    libpcsclite1
ADD utils/yubihsm-setup /shared
RUN sudo bash -xc /shared/resources/release/build-pkg.sh

# install PYTHON3, PIP
RUN sudo apt-get install -y \
    python3 \
    python3-pip

RUN sudo pip install --upgrade pip

ADD utils/Scripts /Scripts
RUN sudo pip install -r /Scripts/AGCertificateProvisioner/requirements.txt

RUN sudo ln -s /usr/bin/python3.8 /usr/local/bin/python
RUN python --version && pip --version

# OTHER
RUN sudo apt-get update
RUN sudo apt-get install -y \
    tree \
    jq \
    zip \
    unzip

WORKDIR /tmp/
RUN sudo rm -rf /var/lib/apt/lists/*

# SET TIMEZONE
ENV TZ="Asia/Taipei"

#SET UP ENVIRONMEN
ENV KTMR_HOME=/home/mt/mt
ENV KTMR_SRC=${KTMR_HOME}/src
ENV LBB_HOME=${KTMR_SRC}/embedded/ca-18952385

ARG UNAME=mt
ARG UID=1000
ARG GID=1000

RUN groupadd --gid $GID $UNAME
RUN useradd -m -u $UID -g $GID -s /bin/sh $UNAME

# SET UP MISCELLANEOUS
RUN mkdir -p $LBB_HOME
WORKDIR $LBB_HOME

RUN echo 'mt    ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
RUN touch /home/$UNAME/.sudo_as_admin_successful

RUN chown -R $UNAME:$UNAME $LBB_HOME
RUN chown -R $UNAME:$UNAME /tmp

USER $UNAME

COPY --chown=$UID:$GID docker/entrypoint.sh /usr/bin/entrypoint.sh
ENTRYPOINT [ "entrypoint.sh" ]
