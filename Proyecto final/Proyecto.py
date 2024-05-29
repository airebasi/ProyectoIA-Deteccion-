import cv2
from PIL import Image, ImageTk
import torch
import time
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

# Inicializa YOLOv5
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

# Variables globales
selected_photo_path = None
current_photo_path = None
previous_object_name = None
root = None
processing_frames = True  # Variable para controlar el procesamiento de frames

# Función para detectar objetos en el frame
def detect_objects(frame, area_of_interest):
    # Corta el área de interés del frame
    x1, y1, x2, y2 = area_of_interest
    cropped_frame = frame[y1:y2, x1:x2]

    # Convierte el frame a color (Requerimiento de YOLOv5)
    frame_rgb = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(frame_rgb)
    
    # Ejecuta la detección de objetos
    results = model(pil_img)
    return results, cropped_frame

# Función para mostrar la imagen seleccionada
def select_photo(object_name, detected_object):
    global selected_photo_path
    selected_photo_path = filedialog.askopenfilename(initialdir=photo_directory, title="Seleccionar foto", filetypes=[("Archivos de imagen", "*.jpg;*.png")])
    if selected_photo_path:
        replace_detection(object_name, detected_object)

# Función para actualizar la preview
def update_preview(old_photo_path, new_photo_path=None):
    # Abre la imagen con PIL
    old_pil_img = Image.open(old_photo_path)
    old_pil_img = old_pil_img.resize((100, 100), Image.LANCZOS)
    old_preview_img = ImageTk.PhotoImage(old_pil_img)
    
    # Actualiza la imagen y su nombre
    preview_label_old.config(image=old_preview_img)
    preview_label_old.image = old_preview_img
    
    # Abre la imagen con PIL
    if new_photo_path:
        new_pil_img = Image.open(new_photo_path)
        new_pil_img = new_pil_img.resize((100, 100), Image.LANCZOS)
        new_preview_img = ImageTk.PhotoImage(new_pil_img)
        
        # Actualiza la imagen del preview con la foto nueva
        preview_label_new.config(image=new_preview_img)
        preview_label_new.image = new_preview_img

# Función para validar el precio ingresado
def is_valid_price(price_str):
    try:
        float(price_str)
        return True
    except ValueError:
        return False

# Función para mostrar una ventana emergente para ingresar el precio
def get_price(object_name, detected_object):
    price_window = tk.Toplevel(root)
    price_window.title(f"Ingrese el precio para {object_name}")
    
    label_price = tk.Label(price_window, text="Precio:")
    label_price.pack()
    entry_price = tk.Entry(price_window)
    entry_price.pack()
    
    # Función para guardar el precio ingresado
    def save_price():
        price_str = entry_price.get()
        if price_str.strip() and is_valid_price(price_str):  # Verifica si la cadena contiene solo números
            price = float(price_str)

            # Guarda los objetos detectados
            photo_path = os.path.join(photo_directory, f"{object_name}.jpg")
            cv2.imwrite(photo_path, detected_object)

            # Guarda el precio
            with open(os.path.join(photo_directory, f"{object_name}_price.txt"), 'w') as f:
                f.write(str(price))

            current_photo_path = photo_path
            update_preview(current_photo_path)
            messagebox.showinfo("Información", "Detección guardada exitosamente.")
            price_window.destroy()
        else:
            # Muestra un mensaje de error si no se ingresó un valor numérico
            messagebox.showerror("Error", "Por favor, ingrese un precio válido para el objeto.")

    save_button = tk.Button(price_window, text="Guardar", command=save_price)
    save_button.pack()

# Función para reemplazar la detección existente o guardar como nuevo
def replace_detection(object_name, detected_object):
    global selected_photo_path
    global current_photo_path
    global previous_object_name
    global root
    global processing_frames
    
    processing_frames = False  # Detiene el procesamiento de frames
    
    photo_path = os.path.join(photo_directory, f"{object_name}.jpg")
    
    # Si el objeto ya existe, muestra la foto
    if os.path.exists(photo_path):
        existing_pil_img = Image.open(photo_path)
        existing_pil_img = existing_pil_img.resize((200, 200), Image.LANCZOS)
        existing_preview_img = ImageTk.PhotoImage(existing_pil_img)

        # Crea una ventana nueva para mostrar la imagen actual
        preview_window = tk.Toplevel(root)
        preview_window.title(f"Imagen existente de {object_name}")
        existing_label = tk.Label(preview_window, image=existing_preview_img)
        existing_label.pack()
        
        # Muestra el precio debajo de la foto existente
        price_path = os.path.join(photo_directory, f"{object_name}_price.txt")
        if os.path.exists(price_path):
            with open(price_path, 'r') as f:
                price = f.read()
            price_label = tk.Label(preview_window, text=f"Precio: {price}")
            price_label.pack()
        
        # Si decide reemplazarlo por uno existente
        def replace_or_save():
            if messagebox.askyesno("Confirmación", f"¿Deseas reemplazar la imagen existente de {object_name}?"):
                cv2.imwrite(photo_path, detected_object)
                current_photo_path = photo_path
                update_preview(current_photo_path)
                messagebox.showinfo("Información", "Detección reemplazada exitosamente.")
            # Si decide guardarlo como uno nuevo
            else:
                get_price(object_name, detected_object)

            # Cierra la ventana
            preview_window.destroy()
            processing_frames = True  # Reanuda el procesamiento de frames

        # Botones para el usuario
        replace_button = tk.Button(preview_window, text="Reemplazar", command=replace_or_save)
        cancel_button = tk.Button(preview_window, text="Cancelar", command=cancel_selection)
        replace_button.pack(side="left", padx=10, pady=10)
        cancel_button.pack(side="right", padx=10, pady=10)

        # Mantiene la ventana abierta
        preview_window.mainloop()
    else:
        # Si es un objeto nuevo:
        if messagebox.askyesno("Confirmación", f"Se detectó un nuevo objeto: {object_name}. ¿Deseas guardarlo?"):
            get_price(object_name, detected_object)
            processing_frames = True  # Reanuda el procesamiento de frames

    selected_photo_path = None

# Define la funcion callback para el boton
def cancel_selection():
    global selected_photo_path
    selected_photo_path = None

# Area de interes (x1, y1, x2, y2)
area_of_interest_width = 300
area_of_interest_height = 300
area_of_interest_x = 10
area_of_interest_y = 10
area_of_interest = (area_of_interest_x, area_of_interest_y, area_of_interest_x + area_of_interest_width, area_of_interest_y + area_of_interest_height)

# Initialize camera capture
cap = cv2.VideoCapture(0)

# Carga YOLO5
labels = model.names

# Clases excluidas
exclude_classes = ['person', 'dog', 'cat', 'bird']  # Excluding classes 'person', 'dog', and 'cat'

# Deteccion de objetos y su tiempo
objects_detected = {}  # Diccionario para almacenar
photo_interval = 3  # Intervalo para tomar la foto

# Directorio para guardar fotos
photo_directory = "photos"
if not os.path.exists(photo_directory):
    os.makedirs(photo_directory)

# Inicializa Tkinter
root = tk.Tk()
root.withdraw()  # Esconde la ventana de inicio de Tkinter

# Crea el frame para almacenar el nombre del la foto vieja
preview_frame_old = tk.Frame(root)
preview_frame_old.pack(pady=10)

# Crea un texto para mostrar el nombre de la foto vieja
preview_label_old = tk.Label(preview_frame_old)
preview_label_old.pack()

# Crea un frame para almacenar el nombre nuevo de la foto
preview_frame_new = tk.Frame(root)
preview_frame_new.pack(pady=10)

# Crea un texto para mostrar el preview del objeto nuevo
preview_label_new = tk.Label(preview_frame_new)
preview_label_new.pack()

# Interfaz para la introduccion de precio
label_price = tk.Label(root, text="Precio:")
label_price.pack()
entry_price = tk.Entry(root)
entry_price.pack()

# Boton para cancelar la seleccion
cancel_button = tk.Button(root, text="Cancelar", command=cancel_selection)
cancel_button.pack()

# Función para procesar el siguiente frame
def process_frame():
    global processing_frames
    
    if processing_frames:
        ret, frame = cap.read()

        # Dibuja el area de interes
        cv2.rectangle(frame, (area_of_interest_x, area_of_interest_y), (area_of_interest_x + area_of_interest_width, area_of_interest_y + area_of_interest_height), (255, 0, 0), 2)
        cv2.putText(frame, "Area de deteccion de movimiento", (area_of_interest_x, area_of_interest_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Detecta objetos en el area de interes
        detections, _ = detect_objects(frame, area_of_interest)

        # Renderiza la deteccion en el area de interes
        for det in detections.xyxy[0].cpu().numpy():
            label = int(det[5])  # Inidice del texto [label]
            confidence = det[4]  # Porcentaje de confianza
            x1, y1, x2, y2 = map(int, det[:4])  # Coordenadas a integers

            # Obtiene el nombre del objeto detectado
            object_name = labels[label]

            # Verifica que el objeto no esta en las clases excluidas
            if object_name not in exclude_classes:
                # Calcula el centro del cuadro
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                # Verifica si el centro del objeto se encuentra en el area de interes
                if area_of_interest_x <= center_x <= area_of_interest_x + area_of_interest_width and area_of_interest_y <= center_y <= area_of_interest_y + area_of_interest_height:
                    # Dibuja el recuadro y coloca el nombre del objeto en el area de interes
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{object_name} ({confidence:.2f})", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # Verifica si el objeto existe
                    if object_name in objects_detected:
                        # Actualiza el tiempo de deteccion
                        objects_detected[object_name] += 1
                    else:
                        # Agrega el objeto al diccionario
                        objects_detected[object_name] = 1
                        # Captura la region del objeto detectado
                        detected_object = frame[y1:y2, x1:x2]

                        # Espera la ejecucion de una accion (remplazo o guardar) actualizando acorde
                        replace_detection(object_name, detected_object)

        # Muestra el frame del resultado
        cv2.imshow('Deteccion de movimiento y objetos. Presiona Q para salir', frame)

    # Procesa el siguiente frame después de un intervalo
    root.after(10, process_frame)

# Inicia el procesamiento del primer frame
process_frame()

# Muestra la interfaz de usuario de Tkinter
root.mainloop()

# Libera la captura y destruye las ventanas de OpenCV
cap.release()
cv2.destroyAllWindows()
