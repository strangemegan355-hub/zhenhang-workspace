Place TLS certificates here for production nginx:

- `fullchain.pem`
- `privkey.pem`

For internal trial (self-signed):

```bash
sh deploy/nginx/certs/generate-self-signed.sh
```

On Windows without OpenSSL:

```bash
docker run --rm -v "%cd%/deploy/nginx/certs:/certs" alpine/openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /certs/privkey.pem -out /certs/fullchain.pem -subj "/CN=localhost"
```
