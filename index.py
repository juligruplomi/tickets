                    nuevo_gasto = {
                        "id": new_id,
                        "tipo_gasto": tipo_gasto,
                        "descripcion": descripcion,
                        "obra": obra,
                        "importe": round(importe_calculado, 2),
                        "fecha_gasto": data.get('fecha_gasto'),
                        "estado": "pendiente",
                        "creado_por": user['user_id'],
                        "supervisor_asignado": data.get('supervisor_asignado'),
                        "fecha_creacion": datetime.datetime.utcnow().isoformat() + 'Z',
                        "archivos_adjuntos": archivos_adjuntos,
                        "fecha_aprobacion": None,
                        "aprobado_por": None,
                        "kilometros": kilometros,
                        "precio_km": precio_km
                    }
                else:
                    # Para otros tipos de gasto (dieta, aparcamiento, otros)
                    importe = float(data.get('importe', 0))
                    
                    nuevo_gasto = {
                        "id": new_id,
                        "tipo_gasto": tipo_gasto,
                        "descripcion": descripcion,
                        "obra": obra,
                        "importe": importe,
                        "fecha_gasto": data.get('fecha_gasto'),
                        "estado": "pendiente",
                        "creado_por": user['user_id'],
                        "supervisor_asignado": data.get('supervisor_asignado'),
                        "fecha_creacion": datetime.datetime.utcnow().isoformat() + 'Z',
                        "archivos_adjuntos": archivos_adjuntos,
                        "fecha_aprobacion": None,
                        "aprobado_por": None,
                        "kilometros": None,
                        "precio_km": None
                    }
                
                # Validar límites
                tipo_config = next((t for t in SYSTEM_CONFIG['gastos']['tipos_gasto'] if t['id'] == nuevo_gasto['tipo_gasto']), None)
                if tipo_config and nuevo_gasto['importe'] > tipo_config['limite_diario']:
                    self._send_json_response({
                        "error": f"El importe supera el límite diario de {tipo_config['limite_diario']}€ para {tipo_config['nombre']}"
                    }, 400)
                    return
                
                GASTOS_DB[new_id] = nuevo_gasto
                self._send_json_response(nuevo_gasto, 201)
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_PUT(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            data = self._get_request_data()
            
            user = self._verify_token()
            if not user:
                self._send_json_response({"error": "Token requerido"}, 401)
                return
                
            if path == '/config/language':
                # Cambiar idioma del usuario
                nuevo_idioma = data.get('language')
                if not nuevo_idioma:
                    self._send_json_response({"error": "Idioma requerido"}, 400)
                    return
                    
                # Verificar que el idioma esté disponible
                if nuevo_idioma not in SYSTEM_CONFIG['idioma']['idiomas_disponibles']:
                    self._send_json_response({"error": "Idioma no disponible"}, 400)
                    return
                    
                # Actualizar idioma del usuario
                user_data = next((u for u in USERS_DB.values() if u['id'] == user['user_id']), None)
                if user_data:
                    user_data['idioma_preferido'] = nuevo_idioma
                    
                # Devolver nueva configuración con traducciones del idioma seleccionado
                updated_config = {
                    "empresa": SYSTEM_CONFIG["empresa"],
                    "gastos": SYSTEM_CONFIG["gastos"],
                    "idioma": {
                        "actual": nuevo_idioma,
                        "disponibles": SYSTEM_CONFIG["idioma"]["idiomas_disponibles"],
                        "traducciones": SYSTEM_CONFIG["idioma"]["traducciones"].get(nuevo_idioma, SYSTEM_CONFIG["idioma"]["traducciones"]["es"])
                    },
                    "apariencia": SYSTEM_CONFIG["apariencia"]
                }
                self._send_json_response(updated_config)
                
            elif path == '/config/admin':
                # Actualizar configuración del sistema
                if user['role'] != 'administrador':
                    self._send_json_response({"error": "Sin permisos para modificar configuración"}, 403)
                    return
                
                # Actualizar SYSTEM_CONFIG con los nuevos datos
                if 'empresa' in data:
                    SYSTEM_CONFIG['empresa'].update(data['empresa'])
                if 'gastos' in data:
                    SYSTEM_CONFIG['gastos'].update(data['gastos'])
                if 'idioma' in data:
                    SYSTEM_CONFIG['idioma'].update(data['idioma'])
                if 'apariencia' in data:
                    SYSTEM_CONFIG['apariencia'].update(data['apariencia'])
                
                # Devolver configuración actualizada
                updated_config = {
                    "success": True,
                    "message": "Configuración actualizada correctamente",
                    "config": {
                        "empresa": SYSTEM_CONFIG["empresa"],
                        "gastos": SYSTEM_CONFIG["gastos"],
                        "idioma": SYSTEM_CONFIG["idioma"],
                        "apariencia": SYSTEM_CONFIG["apariencia"]
                    }
                }
                self._send_json_response(updated_config)
                
            elif path.startswith('/gastos/') and '/aprobar' in path:
                # Aprobar gasto
                gasto_id = int(path.split('/')[-2])
                if gasto_id not in GASTOS_DB:
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
                    return
                    
                gasto = GASTOS_DB[gasto_id]
                
                # Verificar permisos de aprobación
                if user['role'] not in ['supervisor', 'administrador', 'contabilidad']:
                    self._send_json_response({"error": "Sin permisos para aprobar gastos"}, 403)
                    return
                    
                # Verificar límites de aprobación
                limite = SYSTEM_CONFIG['gastos']['limites_aprobacion'].get(user['role'], 0)
                if gasto['importe'] > limite:
                    self._send_json_response({"error": f"El importe supera tu límite de aprobación ({limite}€)"}, 403)
                    return
                    
                accion = data.get('accion')  # 'aprobar' o 'rechazar'
                observaciones = data.get('observaciones', '')
                
                if accion == 'aprobar':
                    gasto['estado'] = 'aprobado'
                elif accion == 'rechazar':
                    gasto['estado'] = 'rechazado'
                else:
                    self._send_json_response({"error": "Acción no válida"}, 400)
                    return
                
                gasto['fecha_aprobacion'] = datetime.datetime.utcnow().isoformat() + 'Z'
                gasto['aprobado_por'] = user['user_id']
                gasto['observaciones'] = observaciones
                
                self._send_json_response(gasto)
                
            elif path.startswith('/gastos/'):
                # Actualizar gasto
                gasto_id = int(path.split('/')[-1])
                if gasto_id not in GASTOS_DB:
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
                    return
                    
                gasto = GASTOS_DB[gasto_id]
                
                # Solo el creador o admin puede editar
                if user['role'] != 'administrador' and gasto['creado_por'] != user['user_id']:
                    self._send_json_response({"error": "Sin permisos para editar este gasto"}, 403)
                    return
                    
                # No se puede editar si ya está aprobado o pagado
                if gasto['estado'] in ['aprobado', 'pagado']:
                    self._send_json_response({"error": "No se puede editar un gasto aprobado o pagado"}, 400)
                    return
                    
                # Actualizar campos
                for key, value in data.items():
                    if key in ['descripcion', 'obra', 'importe', 'fecha_gasto', 'tipo_gasto', 'archivos_adjuntos', 'kilometros', 'precio_km']:
                        gasto[key] = value
                
                # Recalcular importe si es combustible y se proporcionan km/precio
                if gasto['tipo_gasto'] == 'gasolina' and 'kilometros' in data and 'precio_km' in data:
                    gasto['importe'] = round(float(data['kilometros']) * float(data['precio_km']), 2)
                        
                self._send_json_response(gasto)
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_DELETE(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            user = self._verify_token()
            if not user:
                self._send_json_response({"error": "Token requerido"}, 401)
                return
                
            if path.startswith('/gastos/'):
                gasto_id = int(path.split('/')[-1])
                if gasto_id not in GASTOS_DB:
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
                    return
                
                gasto = GASTOS_DB[gasto_id]
                
                # Solo admin o el creador pueden eliminar
                if user['role'] != 'administrador' and gasto['creado_por'] != user['user_id']:
                    self._send_json_response({"error": "Sin permisos para eliminar este gasto"}, 403)
                    return
                    
                # No se puede eliminar si está aprobado o pagado
                if gasto['estado'] in ['aprobado', 'pagado']:
                    self._send_json_response({"error": "No se puede eliminar un gasto aprobado o pagado"}, 400)
                    return
                    
                del GASTOS_DB[gasto_id]
                self._send_json_response({"message": "Gasto eliminado"})
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

handler = GastosAPI