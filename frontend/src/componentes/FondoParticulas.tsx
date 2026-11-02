import React, { useEffect, useRef } from 'react';

/**
 * Fondo de partículas interactivo, dibujado en un <canvas> sin librerías.
 * Las partículas flotan, se unen con líneas cuando están cerca y reaccionan al puntero:
 * se apartan de él y se enlazan con él. El color sale del tema (--c-particula):
 * negro en modo claro y gris plateado en modo oscuro.
 * Con "reducir movimiento" activado en el sistema se dibujan quietas.
 */

interface Particula {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
}

const DISTANCIA_ENLACE = 130;
const RADIO_PUNTERO = 160;

function leerColor(): { rgb: string; opacidad: number; acento: string } {
  const estilo = getComputedStyle(document.documentElement);
  return {
    rgb: estilo.getPropertyValue('--c-particula').trim() || '13, 15, 14',
    opacidad: parseFloat(estilo.getPropertyValue('--particula-opacidad')) || 0.55,
    acento: estilo.getPropertyValue('--c-acento').trim() || '#16A34A',
  };
}

export const FondoParticulas: React.FC<{ className?: string }> = ({ className = '' }) => {
  const lienzoRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const lienzo = lienzoRef.current;
    const ctx = lienzo?.getContext('2d');
    if (!lienzo || !ctx) return;

    const reducirMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let color = leerColor();
    let particulas: Particula[] = [];
    let ancho = 0;
    let alto = 0;
    let cuadro = 0;
    const puntero = { x: -9999, y: -9999, activo: false };

    const crear = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      ancho = window.innerWidth;
      alto = window.innerHeight;
      lienzo.width = ancho * dpr;
      lienzo.height = alto * dpr;
      lienzo.style.width = `${ancho}px`;
      lienzo.style.height = `${alto}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      // Densidad según el área, con tope para no cargar equipos modestos.
      const cantidad = Math.min(110, Math.round((ancho * alto) / 14000));
      particulas = Array.from({ length: cantidad }, () => ({
        x: Math.random() * ancho,
        y: Math.random() * alto,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.6 + 0.6,
      }));
    };

    const dibujar = () => {
      ctx.clearRect(0, 0, ancho, alto);
      const { rgb, opacidad, acento } = color;

      // Halo verde suave donde está el puntero.
      if (puntero.activo) {
        const halo = ctx.createRadialGradient(puntero.x, puntero.y, 0, puntero.x, puntero.y, RADIO_PUNTERO);
        halo.addColorStop(0, acento + '14');
        halo.addColorStop(1, acento + '00');
        ctx.fillStyle = halo;
        ctx.fillRect(puntero.x - RADIO_PUNTERO, puntero.y - RADIO_PUNTERO, RADIO_PUNTERO * 2, RADIO_PUNTERO * 2);
      }

      for (let i = 0; i < particulas.length; i++) {
        const p = particulas[i];

        if (!reducirMovimiento) {
          // Repulsión del puntero.
          const dx = p.x - puntero.x;
          const dy = p.y - puntero.y;
          const d2 = dx * dx + dy * dy;
          if (puntero.activo && d2 < RADIO_PUNTERO * RADIO_PUNTERO && d2 > 0.01) {
            const d = Math.sqrt(d2);
            const fuerza = (1 - d / RADIO_PUNTERO) * 0.6;
            p.vx += (dx / d) * fuerza * 0.12;
            p.vy += (dy / d) * fuerza * 0.12;
          }
          // Fricción suave hacia la velocidad de deriva.
          p.vx *= 0.985;
          p.vy *= 0.985;
          if (Math.abs(p.vx) < 0.05) p.vx += (Math.random() - 0.5) * 0.03;
          if (Math.abs(p.vy) < 0.05) p.vy += (Math.random() - 0.5) * 0.03;
          p.x += p.vx;
          p.y += p.vy;
          if (p.x < -10) p.x = ancho + 10;
          if (p.x > ancho + 10) p.x = -10;
          if (p.y < -10) p.y = alto + 10;
          if (p.y > alto + 10) p.y = -10;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${rgb}, ${opacidad})`;
        ctx.fill();

        // Enlaces entre partículas cercanas.
        for (let j = i + 1; j < particulas.length; j++) {
          const q = particulas[j];
          const ex = p.x - q.x;
          const ey = p.y - q.y;
          const e2 = ex * ex + ey * ey;
          if (e2 < DISTANCIA_ENLACE * DISTANCIA_ENLACE) {
            const alfa = (1 - Math.sqrt(e2) / DISTANCIA_ENLACE) * opacidad * 0.35;
            ctx.strokeStyle = `rgba(${rgb}, ${alfa})`;
            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.stroke();
          }
        }

        // Enlaces con el puntero.
        if (puntero.activo) {
          const mx = p.x - puntero.x;
          const my = p.y - puntero.y;
          const m2 = mx * mx + my * my;
          const alcance = RADIO_PUNTERO * 1.25;
          if (m2 < alcance * alcance) {
            const alfa = (1 - Math.sqrt(m2) / alcance) * opacidad * 0.7;
            ctx.strokeStyle = `rgba(${rgb}, ${alfa})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(puntero.x, puntero.y);
            ctx.stroke();
          }
        }
      }
    };

    const bucle = () => {
      dibujar();
      cuadro = requestAnimationFrame(bucle);
    };

    const alMover = (e: PointerEvent) => {
      puntero.x = e.clientX;
      puntero.y = e.clientY;
      puntero.activo = true;
    };
    const alSalir = () => {
      puntero.activo = false;
      puntero.x = -9999;
      puntero.y = -9999;
    };
    const alRedimensionar = () => {
      crear();
      if (reducirMovimiento) dibujar();
    };
    const alCambiarVisibilidad = () => {
      cancelAnimationFrame(cuadro);
      if (!document.hidden && !reducirMovimiento) cuadro = requestAnimationFrame(bucle);
    };

    // Cuando cambia el tema (clase .dark en <html>) se vuelve a leer el color.
    const observador = new MutationObserver(() => {
      color = leerColor();
      if (reducirMovimiento) dibujar();
    });
    observador.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

    crear();
    if (reducirMovimiento) {
      dibujar();
    } else {
      cuadro = requestAnimationFrame(bucle);
      window.addEventListener('pointermove', alMover, { passive: true });
      document.addEventListener('pointerleave', alSalir);
      window.addEventListener('blur', alSalir);
    }
    window.addEventListener('resize', alRedimensionar);
    document.addEventListener('visibilitychange', alCambiarVisibilidad);

    return () => {
      cancelAnimationFrame(cuadro);
      observador.disconnect();
      window.removeEventListener('pointermove', alMover);
      document.removeEventListener('pointerleave', alSalir);
      window.removeEventListener('blur', alSalir);
      window.removeEventListener('resize', alRedimensionar);
      document.removeEventListener('visibilitychange', alCambiarVisibilidad);
    };
  }, []);

  return (
    <canvas
      ref={lienzoRef}
      aria-hidden="true"
      className={`fixed inset-0 pointer-events-none z-0 ${className}`}
    />
  );
};
