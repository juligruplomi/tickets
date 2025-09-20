                self._send_json_response({"message": "Configuración actualizada", "config": SYSTEM_CONFIG})
                
            elif path.startswith('/tickets/'):
                ticket_id = int(path.split('/')[-1])
                if ticket_id not in TICKETS_DB:
                    self._send_json_response({"error": "Ticket no encontrado"}, 404)
                    return
                    
                ticket = TICKETS_DB[ticket_id]
                
                if user['role'] != 'admin' and ticket['creado_por'] != user['user_id']:
                    self._send_json_response({"error": "Sin permisos para editar este ticket"}, 403)
                    return
                    
                for key, value in data.items():
                    if key in ['titulo', 'descripcion', 'estado', 'prioridad', 'asignado_a', 'categoria']:
                        ticket[key] = value
                        
                self._send_json_response(ticket)
                
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
                
            if path.startswith('/tickets/'):
                ticket_id = int(path.split('/')[-1])
                if ticket_id not in TICKETS_DB:
                    self._send_json_response({"error": "Ticket no encontrado"}, 404)
                    return
                
                if user['role'] != 'admin':
                    self._send_json_response({"error": "Solo administradores pueden eliminar tickets"}, 403)
                    return
                    
                del TICKETS_DB[ticket_id]
                self._send_json_response({"message": "Ticket eliminado"})
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

handler = TicketsAPI