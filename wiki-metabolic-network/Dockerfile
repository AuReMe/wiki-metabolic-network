#This file is part of padmet-utils.
#
#padmet-utils is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#padmet-utils is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with padmet-utils. If not, see <http://www.gnu.org/licenses/>.


FROM mediawiki:1.32
MAINTAINER "Meziane A."
LABEL Vendor="INRIA-Dyliss team"
LABEL Description="MediaWiki for metabolic networks"


# Update repositories & install packages
RUN apt-get update;\
    apt-get install -y -q\
    wget \
    vim \
    imagemagick \
    git \
    software-properties-common \
    make \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libsecret-1-dev \
    mysql-client; \
    apt-get -y -q clean; \
    apt-get -y -q autoremove

#Remove old wiki data and replace by new
RUN rm -rf /var/www/html/*;\
    mkdir /home/template
COPY wiki_template /home/template/wiki_template

# Install python 3.7
RUN cd /usr/src;\
    wget https://www.python.org/ftp/python/3.7.2/Python-3.7.2.tgz;\
    tar xzf Python-3.7.2.tgz;\
    cd Python-3.7.2;\
    ./configure --enable-optimizations;\
    make altinstall

# Install python libs
RUN pip3.7 install --upgrade pip;\
    pip3 install git+https://github.com/mezianeAITE/aiowiki@userrights;\
    pip3.7 install docopt

# Install composer for semanticMediaWiki
RUN cd /tmp;\
    php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"\
    php -r "if (hash_file('sha384', 'composer-setup.php') === '48e3236262b34d30969dca3c37281b3b4bbe3221bda826ac6a9a62d6444cdb0dcd0615698a5cbe587c3f0fe57a54d8f5') { echo 'Installer verified'; } else { echo 'Installer corrupt'; unlink('composer-setup.php'); } echo PHP_EOL;";\
    php composer-setup.php;\
    php -r "unlink('composer-setup.php');";\
    mv composer.phar /usr/bin/composer

#
COPY wiki wiki_load /usr/bin/
COPY wiki_config.txt /home/
COPY forms /home/forms/
RUN chmod +x /usr/bin/wiki
RUN chmod +x /usr/bin/wiki_load



