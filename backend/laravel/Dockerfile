FROM php:8.3-apache

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev unzip     && docker-php-ext-install pdo_pgsql     && a2enmod rewrite headers     && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer
WORKDIR /var/www/html
COPY . .
RUN composer install --no-dev --prefer-dist --no-interaction --optimize-autoloader     && sed -ri 's!/var/www/html!/var/www/html/public!g' /etc/apache2/sites-available/000-default.conf     && printf '\n<Directory /var/www/html/public>\n    AllowOverride All\n    Require all granted\n</Directory>\n' >> /etc/apache2/apache2.conf     && sed -ri 's/^Listen 80$/Listen 10000/' /etc/apache2/ports.conf     && sed -ri 's/:80>/:10000>/' /etc/apache2/sites-available/000-default.conf     && chown -R www-data:www-data storage bootstrap/cache

COPY docker/start.sh /usr/local/bin/start-laravel
RUN chmod +x /usr/local/bin/start-laravel

ENV PORT=10000
EXPOSE 10000
CMD ["start-laravel"]