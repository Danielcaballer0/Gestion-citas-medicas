# Guía de Configuración de CreativeCollaborator

## Solución a problemas de integración

### Error de redirección con Google Calendar

El error "redirect_uri_mismatch" que aparece al intentar conectar con Google Calendar ha sido solucionado. El problema era que la aplicación estaba buscando un archivo de credenciales con nombre incorrecto.

**Pasos para configurar Google Calendar correctamente:**

1. Asegúrate de que el archivo `client_secret_678559980772-kftgco67hmaflpdvhetp9ji96s1bcjqe.apps.googleusercontent.com.json` esté en la raíz del proyecto.

2. Verifica que la URI de redirección en la consola de Google API coincida exactamente con:
   ```
   http://localhost:5000/client/google/oauth2callback
   ```

3. Si necesitas cambiar el puerto o la URL, deberás actualizar también la URI de redirección en el archivo de credenciales de Google.

### Configuración de la pasarela de pago (Stripe)

Para que la pasarela de pago funcione correctamente, necesitas configurar las claves API de Stripe:

1. Regístrate en [Stripe](https://dashboard.stripe.com/register) si aún no tienes una cuenta.

2. Obtén tus claves API desde el [Dashboard de Stripe](https://dashboard.stripe.com/apikeys).

3. Copia el archivo `.env.example` a `.env` si aún no lo has hecho:
   ```
   copy .env.example .env
   ```

4. Edita el archivo `.env` y añade tus claves de Stripe:
   ```
   STRIPE_SECRET_KEY=sk_test_tu_clave_secreta_de_stripe
   STRIPE_PUBLISHABLE_KEY=pk_test_tu_clave_publica_de_stripe
   ```

5. Reinicia la aplicación para que los cambios surtan efecto.

## Variables de entorno

La aplicación utiliza las siguientes variables de entorno que puedes configurar en el archivo `.env`:

- `SESSION_SECRET`: Clave secreta para las sesiones de Flask
- `STRIPE_SECRET_KEY`: Clave secreta de API de Stripe
- `STRIPE_PUBLISHABLE_KEY`: Clave pública de API de Stripe
- `GOOGLE_CLIENT_ID`: ID de cliente de Google API
- `GOOGLE_CLIENT_SECRET`: Secreto de cliente de Google API
- `SENDGRID_API_KEY`: Clave API de SendGrid para envío de emails
- `MAIL_DEFAULT_SENDER`: Dirección de correo electrónico del remitente

## Inicialización de la base de datos

Para inicializar las especialidades en la base de datos, ejecuta:

```
python init_specialties.py
```

Esto creará las especialidades básicas necesarias para el registro de profesionales.