FROM gitpod/workspace-base:latest
ENV PATH=$HOME/gnat/bin:$PATH\
    GPR_PROJECT_PATH=/home/gitpod/adalib/share/gpr:\
    LIBRARY_TYPE=static

RUN sudo apt-get update \
 && sudo apt-get install -y \
    libx11-xcb1 \
    python3 python3-pip \
 && curl -SL https://community.download.adacore.com/v1/a639696a9fd3bdf0be21376cc2dc3129323cbe42?filename=gnat-2020-20200818-x86_64-linux-bin \
  --output /tmp/gnat-2020-20200818-x86_64-linux-bin \
 && chmod +x /tmp/gnat-2020-20200818-x86_64-linux-bin \
 && /tmp/gnat-2020-20200818-x86_64-linux-bin \
   --platform minimal --script /tmp/gnat_install.qs InstallPrefix=$HOME/gnat \
 && sudo apt-get purge -y --auto-remove libx11-xcb1 \
 && sudo apt-get clean \
 && sudo rm -rf /var/lib/apt/lists/* \
 && sudo /usr/bin/pip3 install e3-testsuite
