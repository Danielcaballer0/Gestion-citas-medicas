# Integración de PayPal en Gestor de Citas

Este documento describe cómo configurar y utilizar PayPal como pasarela de pago en la aplicación Gestor de Citas.

## Requisitos Previos

Para integrar PayPal, necesitarás:

1. Una cuenta de PayPal Business (puede ser una cuenta Sandbox para desarrollo)
2. Credenciales de API de PayPal (Client ID y Secret)

## Configuración

### 1. Obtener Credenciales de API

1. Inicia sesión en el [Panel de Desarrolladores de PayPal](https://developer.paypal.com/dashboard/)
2. Crea una nueva aplicación (o usa una existente)
3. Obtén el **Client ID** y el **Secret** de la aplicación

### 2. Configurar Variables de Entorno

Agrega las siguientes variables a tu archivo `.env`:

```
PAYPAL_CLIENT_ID=tu_client_id_de_paypal
PAYPAL_CLIENT_SECRET=tu_secret_de_paypal
PAYPAL_PRODUCTION=false  # Cambiar a true en producción
PAYMENT_GATEWAY=paypal   # Cambiar a paypal para usar PayPal como pasarela predeterminada
```

## Funcionamiento

La integración de PayPal permite:

1. **Procesar pagos**: Los clientes pueden pagar sus citas utilizando PayPal
2. **Reembolsos**: Se pueden procesar reembolsos automáticos para citas canceladas
3. **Webhooks**: Procesamiento automático de notificaciones de pago

## Flujo de Pago

1. El cliente selecciona una cita y procede al pago
2. El sistema redirige al cliente a la página de pago de PayPal
3. El cliente completa el pago en PayPal
4. PayPal redirige al cliente de vuelta a la aplicación
5. La aplicación confirma el pago y actualiza el estado de la cita

## Configuración de Webhooks (Producción)

Para recibir notificaciones automáticas de PayPal:

1. En el Panel de Desarrolladores de PayPal, configura un webhook
2. Establece la URL del webhook a: `https://tu-dominio.com/payment/webhook/paypal`
3. Selecciona los eventos `PAYMENT.CAPTURE.COMPLETED` y otros eventos relevantes

## Solución de Problemas

- **Pagos no procesados**: Verifica las credenciales de API y el modo (sandbox/producción)
- **Errores de webhook**: Asegúrate de que la URL del webhook sea accesible públicamente
- **Problemas de reembolso**: Verifica que el ID de captura esté disponible en la respuesta de la orden

## Recursos Adicionales

- [Documentación de PayPal REST API](https://developer.paypal.com/docs/api/overview/)
- [Guía de Integración de PayPal Checkout](https://developer.paypal.com/docs/checkout/)