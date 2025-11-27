


def exportar_usuarios_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Usuarios"

    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from datetime import datetime

    # Encabezado principal de la tienda (NARANJA)
    ws.merge_cells('A1:E1')
    ws['A1'] = 'TIENDA NATURISTA LOS GIRASOLES'
    ws['A1'].font = Font(bold=True, size=16, color='FFFFFF')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A1'].fill = PatternFill(start_color='E67E22', end_color='E67E22', fill_type='solid')
    ws.row_dimensions[1].height = 30

    # Subtítulo (NARANJA OSCURO)
    ws.merge_cells('A2:E2')
    ws['A2'] = 'LISTADO DE USUARIOS'
    ws['A2'].font = Font(bold=True, size=12, color='FFFFFF')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A2'].fill = PatternFill(start_color='D35400', end_color='D35400', fill_type='solid')
    ws.row_dimensions[2].height = 25

    # Fecha de generación
    ws.merge_cells('A3:E3')
    ws['A3'] = f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    ws['A3'].font = Font(italic=True, size=10)
    ws['A3'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[3].height = 20

    # Fila vacía
    ws.append([])

    # Encabezados de columnas (fila 5)
    encabezados = ["ID", "Nombre", "Email", "Rol", "Teléfono"]
    ws.append(encabezados)

    # Estilo para encabezados de columnas (AMARILLO)
    header_fill = PatternFill(start_color='F1C40F', end_color='F1C40F', fill_type='solid')
    header_font = Font(bold=True, color='000000')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for col in range(1, 6):
        cell = ws.cell(row=5, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    # Datos de usuarios
    row_num = 6
    for u in Usuario.objects.all():
        ws.append([u.id, u.nombre, u.email, u.rol, u.phone_number])
        
        for col in range(1, 6):
            cell = ws.cell(row=row_num, column=col)
            cell.border = thin_border
        
        row_num += 1

    # Ajustar ancho de columnas
    column_widths = [10, 30, 35, 15, 20]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename="usuarios.xlsx"'
    wb.save(response)

    return response

def exportar_pedidos_excel(request):
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from datetime import datetime

    wb = Workbook()
    ws = wb.active
    ws.title = "Pedidos"

    # Encabezado principal (NARANJA)
    ws.merge_cells('A1:F1')
    ws['A1'] = 'TIENDA NATURISTA LOS GIRASOLES'
    ws['A1'].font = Font(bold=True, size=16, color='FFFFFF')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A1'].fill = PatternFill(start_color='E67E22', end_color='E67E22', fill_type='solid')
    ws.row_dimensions[1].height = 30

    # Subtítulo (NARANJA OSCURO)
    ws.merge_cells('A2:F2')
    ws['A2'] = 'LISTADO DE PEDIDOS'
    ws['A2'].font = Font(bold=True, size=12, color='FFFFFF')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A2'].fill = PatternFill(start_color='D35400', end_color='D35400', fill_type='solid')
    ws.row_dimensions[2].height = 25

    # Fecha de generación
    ws.merge_cells('A3:F3')
    ws['A3'] = f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    ws['A3'].font = Font(italic=True, size=10)
    ws['A3'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[3].height = 20

    # Fila vacía
    ws.append([])

    # Encabezados de columnas (AMARILLO)
    encabezados = ['ID', 'Cliente', 'Email', 'Fecha', 'Estado', 'Total']
    ws.append(encabezados)

    header_fill = PatternFill(start_color='F1C40F', end_color='F1C40F', fill_type='solid')
    header_font = Font(bold=True, color='000000')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for col in range(1, 7):
        cell = ws.cell(row=5, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    # Filtros desde GET
    estado = request.GET.get('estado')
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    # Consulta base
    pedidos = Pedido.objects.filter(pago=True).order_by('-fecha_creacion')
    
    if estado:
        pedidos = pedidos.filter(estado=estado)
    if mes:
        pedidos = pedidos.filter(fecha_creacion__month=mes)
    if anio:
        pedidos = pedidos.filter(fecha_creacion__year=anio)

    # Colores por estado
    estado_colors = {
        'pendiente': 'FCF3CF',   # Amarillo claro
        'enviado': 'D6EAF8',     # Azul claro
        'entregado': 'D5F4E6',   # Verde claro
    }

    # Datos
    row_num = 6
    total = 0
    for pedido in pedidos:
        ws.append([
            pedido.id,
            pedido.usuario.nombre if pedido.usuario else 'Sin usuario',
            pedido.usuario.email if pedido.usuario else 'Sin email',
            pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            pedido.estado.capitalize(),
            float(pedido.total)
        ])
        total += float(pedido.total)

        # Color según estado
        estado_lower = pedido.estado.lower()
        row_fill = PatternFill(
            start_color=estado_colors.get(estado_lower, 'FFFFFF'),
            end_color=estado_colors.get(estado_lower, 'FFFFFF'),
            fill_type='solid'
        )

        for col in range(1, 7):
            cell = ws.cell(row=row_num, column=col)
            cell.border = thin_border
            cell.fill = row_fill
        row_num += 1

    # Fila de total
    ws.append(['', '', '', '', 'TOTAL:', total])
    total_fill = PatternFill(start_color='E67E22', end_color='E67E22', fill_type='solid')
    for col in range(1, 7):
        cell = ws.cell(row=row_num, column=col)
        cell.border = thin_border
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = total_fill

    # Ajustar ancho de columnas
    column_widths = [10, 25, 30, 20, 15, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="pedidos.xlsx"'
    wb.save(response)
    return response

def exportar_ventas_excel(request):
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from datetime import datetime

    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"

    # Encabezado principal (NARANJA)
    ws.merge_cells('A1:D1')
    ws['A1'] = 'TIENDA NATURISTA LOS GIRASOLES'
    ws['A1'].font = Font(bold=True, size=16, color='FFFFFF')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A1'].fill = PatternFill(start_color='E67E22', end_color='E67E22', fill_type='solid')
    ws.row_dimensions[1].height = 30

    # Subtítulo (NARANJA OSCURO)
    ws.merge_cells('A2:D2')
    ws['A2'] = 'INFORME DE VENTAS'
    ws['A2'].font = Font(bold=True, size=12, color='FFFFFF')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A2'].fill = PatternFill(start_color='D35400', end_color='D35400', fill_type='solid')
    ws.row_dimensions[2].height = 25

    # Fecha de generación
    ws.merge_cells('A3:D3')
    ws['A3'] = f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    ws['A3'].font = Font(italic=True, size=10)
    ws['A3'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[3].height = 20

    # Fila vacía
    ws.append([])

    # Encabezados de columnas (AMARILLO)
    encabezados = ['ID', 'Cliente', 'Fecha', 'Monto']
    ws.append(encabezados)

    header_fill = PatternFill(start_color='F1C40F', end_color='F1C40F', fill_type='solid')
    header_font = Font(bold=True, color='000000')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for col in range(1, 5):
        cell = ws.cell(row=5, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    # Filtros desde GET
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    # Consulta base
    pedidos = Pedido.objects.filter(pago=True, total__gt=0).order_by('-fecha_creacion')
    
    if mes:
        pedidos = pedidos.filter(fecha_creacion__month=mes)
    if anio:
        pedidos = pedidos.filter(fecha_creacion__year=anio)

    # Datos
    row_num = 6
    total = 0
    for pedido in pedidos:
        ws.append([
            pedido.id,
            pedido.usuario.nombre if pedido.usuario else 'Sin usuario',
            pedido.fecha_creacion.strftime('%d/%m/%Y'),
            float(pedido.total)
        ])
        total += float(pedido.total)

        for col in range(1, 5):
            ws.cell(row=row_num, column=col).border = thin_border
        row_num += 1

    # Fila de total (AMARILLO CLARO)
    ws.append(['', '', 'TOTAL:', total])
    total_fill = PatternFill(start_color='FCF3CF', end_color='FCF3CF', fill_type='solid')
    for col in range(1, 5):
        cell = ws.cell(row=row_num, column=col)
        cell.border = thin_border
        cell.font = Font(bold=True)
        cell.fill = total_fill

    # Ajustar ancho de columnas
    column_widths = [10, 30, 15, 20]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="informe_ventas.xlsx"'
    wb.save(response)
    return response