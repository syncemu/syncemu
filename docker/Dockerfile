FROM ubuntu:22.04 as syncemu

ENV DEBIAN_FRONTEND=noninteractive

# Enable APT package caching
RUN rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

    RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && apt install -y --no-install-recommends \
      vim \
      bc \
      libncurses-dev \
      git \
      gcc-9 \
      g++-9 \
      g++-9-aarch64-linux-gnu \
      clang-format \
      openssh-client \
      make \
      unzip \
      wget \
      libblkid-dev \
      curl \
      virtualenv \
      python-is-python3 \
      python3-dev \
      python-setuptools \
      python3-poetry \
      cmake \
      gdb-multiarch \
      ninja-build \
      pkg-config \
      libglib2.0-dev \
      meson \
      libpixman-1-dev \
      python3.10-venv \
      tzdata \
      qemu-utils \
      bzip2 \
      tar \
      software-properties-common \
      build-essential \
      python3-cachecontrol \
      netcat

# set gcc 9 as default
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 60 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 60 && \
    update-alternatives --install /usr/bin/cc cc /usr/bin/gcc-9 60

WORKDIR /root

# install poetry for rehosting framework
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH=/root/.local/bin/:$PATH

# install rehosting framework
RUN --mount=type=bind,source=./src,target=/src,rw \
   cd /src/syncemu-rehosting && poetry install

# install avatar2 cfg file to set paths for QEMU and gdb
RUN mkdir .avatar2
COPY docker/settings.cfg /root/.avatar2/

# Build avatar-qemu
RUN --mount=type=bind,source=./src,target=/src,rw \
    cd /src/avatar-qemu/ && mkdir -p build && \
    cd /src/avatar-qemu/build && \
    ../configure --disable-sdl --target-list=arm-softmmu,aarch64-softmmu && \
    make -j"$(nproc --ignore=1)" && \
    make install

WORKDIR /root
# Get Android platform tools
RUN mkdir Android
RUN wget https://dl.google.com/android/repository/platform-tools-latest-linux.zip
RUN unzip platform-tools-latest-linux.zip -d ./Android/
ENV PATH=/root/Android/platform-tools:$PATH

# add abootimg: abootimg from ubuntu/debian repos does not support some boot.img formats
RUN git clone https://github.com/omicron-io/abootimg.git
RUN make -C abootimg
ENV PATH=/root/abootimg:$PATH

# install Android gcc toolchain
RUN git clone https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/aarch64/aarch64-linux-android-4.9
WORKDIR /root/aarch64-linux-android-4.9
RUN git checkout 945630363f964b219c4b211bb635b61cc8547fc7
ENV PATH=/root/aarch64-linux-android-4.9/bin:$PATH

WORKDIR /src/syncemu-rehosting/

