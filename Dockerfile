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

# Settings
ENV MYSQL_DB_ROOT_PWD="db_wiki_pwd"
ENV MEDIA_WIKI_ARCHIVE="mediawiki-1.32.0.tar.gz"

# Update repositories & install packages
RUN apt-get update;\
    echo mysql-server mysql-server/root_password password $MYSQL_DB_ROOT_PWD | debconf-set-selections;\
    echo mysql-server mysql-server/root_password_again password $MYSQL_DB_ROOT_PWD | debconf-set-selections;\
    apt-get install -y -q\
    wget \
    mysql-server \
    vim \
    imagemagick \
    git \
    software-properties-common \



    apt-get -y -q clean; \
    apt-get -y -q autoremove
RUN pip3 install \
    docopt \
    git+https://github.com/abretaud/ceterach.git
RUN echo 'alias DB="mysql --user=root --password=$MYSQL_DB_ROOT_PWD"' >> ~/.bashrc

# Config Nginx
COPY default /etc/nginx/sites-available/

# Config php5-fpm upload size
RUN sed -i -e 's#upload_max_filesize = 2M#upload_max_filesize = 25M#g' /etc/php/7.2/apache2/php.ini
RUN sed -i -e 's#post_max_size = 8M#post_max_size = 25M#g' /etc/php/7.2/apache2/php.ini

# Config MySQL
RUN expect << END_OF_EXPECT ;\
        set timeout 1\
\
        spawn mysql_secure_installation\
\
        expect {"Enter current password for root (enter for none):"}\
        send "$MYSQL_DB_ROOT_PWD\n"\
\
        expect {Change the root password? [Y/n]}\
        send "n\r"\
\
        expect {Remove anonymous users? [Y/n]}\
        send "y\r"\
\
        expect {Disallow root login remotely? [Y/n]}\
        send "y\r"\
\
        expect {Remove test database and access to it? [Y/n]}\
        send "y\r"\
\
        expect {Reload privilege tables now? [Y/n]}\
        send "y\r"\
\
        expect eof\
END_OF_EXPECT\
#RUN find /var/lib/mysql -type f -exec touch {} \; && service mysql start

# Informs Docker that the container listens on the specified network ports at runtime. 
# EXPOSE does not make the ports of the container accessible to the host
EXPOSE 80 3306

# Command for an 'executing container'
COPY supervisord.conf /etc/supervisor/conf.d/
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
