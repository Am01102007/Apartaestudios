# Frontend · Aura Apartaestudios

React + TypeScript + Vite + Tailwind. Consume la API del backend (`/api/v1`) con la sesión en
cookie HttpOnly y el token CSRF en la cabecera `X-CSRF-Token`; no guarda tokens en el navegador.

```powershell
npm install
npm run dev      # http://localhost:5173, reenvía /api a http://localhost:8000
npm run build    # revisa tipos y compila en dist/
```

Los tipos de `src/api/esquema.d.ts` salen del contrato real de la API. Si cambia el backend:

```powershell
# desde backend/, con la API corriendo en el puerto 8000
Invoke-WebRequest http://localhost:8000/api/openapi.json -OutFile ..\frontend\openapi.json
# desde frontend/
npx openapi-typescript@7 openapi.json -o src/api/esquema.d.ts
npm run build    # los campos que ya no existan aparecen como errores de tipos
```

Producción (Railway): `Dockerfile` compila y sirve con nginx, que reenvía `/api/` al backend.
Variable obligatoria del servicio: `API_URL` = URL pública del backend, sin `/` final.
