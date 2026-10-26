import React from 'react';
import { NOMBRES_TIPO_DOCUMENTO, TIPOS_DOCUMENTO } from '../api/tipos';

/** Opciones de <select> con los tipos de documento que acepta la API. */
export const OpcionesDocumento: React.FC = () => (
  <>
    {TIPOS_DOCUMENTO.map((t) => (
      <option key={t} value={t}>
        {NOMBRES_TIPO_DOCUMENTO[t]} ({t})
      </option>
    ))}
  </>
);
