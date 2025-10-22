# Integración con Google Calendar

## Solución al error redirect_uri_mismatch

Este documento explica cómo se solucionó el error `redirect_uri_mismatch` que ocurría durante la autenticación con Google OAuth 2.0.

### Problema

El error `redirect_uri_mismatch` ocurre cuando la URL de redirección utilizada en la solicitud de autorización no coincide exactamente con una de las URLs de redirección autorizadas configuradas en la consola de Google Cloud para el proyecto.

En nuestro caso, el problema se presentaba porque estábamos usando `url_for('client.oauth2callback', _external=True)` para generar la URL de redirección, lo que podía producir variaciones en la URL dependiendo del entorno (por ejemplo, diferencias en el protocolo, puerto o dominio).

### Solución

La solución implementada consiste en utilizar directamente la URL exacta que está configurada en el archivo de credenciales de Google, en lugar de generarla dinámicamente con Flask:

```python
# Antes (problemático)
flow.redirect_uri = url_for('client.oauth2callback', _external=True)

# Después (solución)
flow.redirect_uri = 'http://localhost:5000/client/google/oauth2callback'
```

Esta modificación se realizó en dos lugares:

1. En la función `get_auth_url()` del archivo `google_calendar_utils.py`
2. En la ruta `oauth2callback()` del archivo `routes/client.py`

### Configuración correcta

Para que la integración funcione correctamente, asegúrate de que:

1. El archivo `client_secret_678559980772-kftgco67hmaflpdvhetp9ji96s1bcjqe.apps.googleusercontent.com.json` esté en la raíz del proyecto.

2. La URI de redirección en la consola de Google Cloud coincida exactamente con:
   ```
   http://localhost:5000/client/google/oauth2callback
   ```

3. Si necesitas cambiar el puerto o la URL, deberás actualizar:
   - La URI de redirección en la consola de Google Cloud
   - El valor de `redirect_uri` en ambos archivos mencionados anteriormente
   - El archivo de credenciales de Google

### Referencia

Para más información sobre este error, consulta la [documentación oficial de Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2/web-server#uri-validation).