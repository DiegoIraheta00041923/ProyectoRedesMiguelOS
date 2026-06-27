# Configuración para el Nivel 1 de la empresa

## 1. Representar el switch de Capa 3 en GNS3

Para este caso se utilizaron routers **Cisco 3725** equipados con el módulo **NM-16ESW** para obtener 16 puertos de switch. Dado que el Nivel 1 cuenta con 17 dispositivos finales, se utilizaron dos equipos (`Switch-Capa3-N1-p1` y `Switch-Capa3-N1-p2`) conectados en cascada para cubrir la demanda de puertos.

Antes de iniciar, se asignó **32 MiB** al **PCMCIA disk0** de cada equipo para permitir el correcto almacenamiento de la base de datos de VLAN.

### Configuración del enlace troncal

#### Switch-Capa3-N1-p1

```bash
enable
configure terminal

interface fastEthernet 1/15
 switchport trunk encapsulation dot1q
 switchport mode trunk
 no shutdown
exit
```

#### Switch-Capa3-N1-p2

```bash
enable
configure terminal

interface fastEthernet 1/15
 switchport trunk encapsulation dot1q
 switchport mode trunk
 no shutdown
exit
```

---

## 2. Crear las VLAN y activar el enrutamiento

Las VLAN deben crearse en ambos equipos para mantener la consistencia de la base de datos.

```bash
configure terminal

vlan 12
 name Ventas
exit

vlan 13
 name At_Cliente
exit

vlan 14
 name Recepcion
exit

vlan 50
 name Empleados_WiFi
exit

vlan 60
 name Invitados_WiFi
exit
```

Únicamente en el **Switch-Capa3-N1-p1** se habilita el enrutamiento y se configuran las interfaces virtuales (SVI), que actuarán como gateway de cada VLAN.

```bash
configure terminal

ip routing

interface vlan 12
 ip address 192.168.50.65 255.255.255.240
 no shutdown
exit

interface vlan 13
 ip address 192.168.50.81 255.255.255.240
 no shutdown
exit

interface vlan 14
 ip address 192.168.50.201 255.255.255.248
 no shutdown
exit

interface vlan 50
 ip address 192.168.50.1 255.255.255.224
 no shutdown
exit

interface vlan 60
 ip address 192.168.50.33 255.255.255.224
 no shutdown
exit
```

---

## 3. Asignación de puertos físicos y dispositivos finales

Se asignan los puertos de acceso para los usuarios y los puertos troncales para los Access Point.

Ejemplo de asignación para la VLAN de **Ventas**:

```bash
configure terminal

interface range fastEthernet 1/0 - 6
 switchport mode access
 switchport access vlan 12
 no shutdown
exit
```

Las direcciones IP de los hosts se asignan directamente desde la consola de cada **VPCS**.

Ejemplo para la primera computadora de Ventas:

```bash
ip 192.168.50.66 /28 192.168.50.65
save
```

---

## 4. Configuración del Backbone (Topología de Malla)

Se utilizan los puertos enrutados nativos del chasis (**FastEthernet 0/0** y **FastEthernet 0/1**) del equipo `Switch-Capa3-N1-p1` para conectar el Nivel 1 con los demás niveles de la red e implementar las rutas estáticas flotantes.

```bash
configure terminal

! Enlace hacia el Nivel 3
interface fastEthernet 0/0
 ip address 192.168.50.241 255.255.255.252
 no shutdown
exit

! Enlace hacia el Nivel 2
interface fastEthernet 0/1
 ip address 192.168.50.233 255.255.255.252
 no shutdown
exit

! Ruta principal
ip route 0.0.0.0 0.0.0.0 192.168.50.242

! Ruta flotante
ip route 0.0.0.0 0.0.0.0 192.168.50.234 10
```
**Nota técnica sobre la estrategia de enrutamiento (Alta Disponibilidad):**

* **Ruta Principal:** Al no especificar una métrica, el router le asigna por defecto una Distancia Administrativa (AD) de **1**. Todo el tráfico del Nivel 1 intentará salir siempre por esta ruta directa hacia el Nivel 3.
* **Ruta Flotante (Contingencia):** Al agregar el número **10** al final del segundo comando, le asignamos una Distancia Administrativa mayor. Al ser un número más alto, el router considera esta ruta como "secundaria" y la mantiene oculta (inactiva) para no saturar la red.
* **Comportamiento ante fallos (Failover):** Si el enlace físico principal hacia el Nivel 3 se corta o el puerto se apaga, el router elimina la ruta principal de su tabla y automáticamente "saca a flote" la ruta de AD 10. Todo el tráfico se desvía en milisegundos a través de la malla hacia el Nivel 2, garantizando la continuidad del negocio sin intervención humana.

---

## 5. Configuración de ACL (Seguridad)

Se implementan listas de control de acceso (ACL) para restringir la comunicación entre departamentos cuando sea necesario.

Ejemplo para la VLAN de **Ventas**:

```bash
configure terminal

ip access-list extended FILTRO_VENTAS
 permit ip 192.168.50.64 0.0.0.15 192.168.50.64 0.0.0.15
 deny ip any 192.168.50.80 0.0.0.15
 deny ip any 192.168.50.200 0.0.0.7
 permit ip any any
exit

interface vlan 12
 ip access-group FILTRO_VENTAS in
exit
```

La misma lógica puede aplicarse a las demás VLAN, modificando las redes de origen y destino
```