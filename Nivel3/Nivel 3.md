# Configuración para el Nivel 3 de la empresa

## 1. Representar el switch de Capa 3 en GNS3

Para este nivel se utilizaron **routers Cisco 3725** configurados con el módulo **NM-16ESW** para simular un switch de capa 3. Debido a la cantidad de puertos necesarios, el switch fue dividido en **tres equipos** conectados mediante **enlaces troncales (Trunk)**, permitiendo transportar las VLAN entre todos ellos.

Los equipos utilizados son:

* **Switch-Capa3-N3-p1**
* **Switch-Capa3-N3-p2**
* **Switch-Capa3-N3-p3**

Antes de comenzar la configuración, en cada equipo se asignan **32 MiB** al **PCMCIA disk0**, lo que permite almacenar correctamente la base de datos de VLAN.

### Configuración de los enlaces troncales

Los puertos que conectan los tres equipos deben configurarse en modo **Trunk** utilizando encapsulación **dot1q**, de manera que todas las VLAN puedan circular entre los switches.

```Switch-Capa3-N3-p1```
```bash
enable
configure terminal

interface fastEthernet1/13
switchport trunk encapsulation dot1q
switchport mode trunk
no shutdown
exit

interface fastEthernet1/15
switchport trunk encapsulation dot1q
switchport mode trunk
no shutdown
exit
```
```Switch-Capa3-N3-p2```
```bash
enable
configure terminal

interface fastEthernet1/14
switchport trunk encapsulation dot1q
switchport mode trunk
no shutdown
exit

interface fastEthernet1/15
switchport trunk encapsulation dot1q
switchport mode trunk
no shutdown
exit
```
```Switch-Capa3-N3-p3```
```bash
enable
configure terminal

interface fastEthernet1/13
switchport trunk encapsulation dot1q
switchport mode trunk
no shutdown
exit

interface fastEthernet1/14
switchport trunk encapsulation dot1q
switchport mode trunk
no shutdown
exit

```


Cada equipo únicamente configura como troncales los puertos utilizados para enlazarse con los demás módulos.

---

## 2. Crear las VLAN y activar el enrutamiento

Las VLAN representan los diferentes departamentos del Nivel 3.

Por ejemplo:

```bash
config terminal
vlan 10
 name Gerencia_General
exit

vlan 20
 name Oficina_IT
exit

vlan 30
 name Soporte_Tecnico
exit

vlan 40
 name Camaras
exit

```

Las VLAN deben crearse **en los tres switches** para mantener la misma base de datos.

Posteriormente, únicamente el **Switch-Capa3-N3-p1** habilita el enrutamiento mediante el comando:

```bash
ip routing
```

Después se crean las **interfaces virtuales (SVI)**, las cuales funcionarán como puerta de enlace (Gateway) para cada una de las VLAN.

Se recomienda utilizar la **primera dirección IP disponible** de cada subred como gateway.

La estructura general es:

```bash
configure terminal

interface vlan [ID_VLAN]
 ip address [IP_GATEWAY] [MASCARA]
 no shutdown
exit
```

Este procedimiento debe repetirse para cada una de las VLAN del nivel.

---

## 3. Asignación de puertos físicos

Una vez creadas las VLAN, se asignan los puertos físicos correspondientes a cada departamento utilizando interfaces de acceso (**Access**).

Para ello se utilizan rangos de interfaces con `interface range`, indicando el número de VLAN que corresponde a cada grupo de dispositivos.

Ejemplo:

```bash
configure terminal

interface range fastEthernet 1/x - y
 switchport mode access
 switchport access vlan [ID_VLAN]
exit
```

Si algún puerto conecta otro switch o un dispositivo que transporte varias VLAN, deberá configurarse como **Trunk**.

Las direcciones IP de las computadoras, teléfonos IP y demás dispositivos finales se configuran directamente desde cada **VPCS**, utilizando como puerta de enlace la dirección configurada en la interfaz virtual de su VLAN.

---


## 5. Configuración de ACL (Seguridad)

Para controlar la comunicación entre departamentos se implementan **Listas de Control de Acceso Extendidas (ACL)**.

La lógica utilizada consiste en:

1. Permitir el tráfico dentro de la misma VLAN.
2. Denegar el acceso hacia las demás VLAN del Nivel 3.
3. Permitir el resto del tráfico para que pueda comunicarse con otros niveles de la red o con Internet.

La estructura utilizada es:

```bash
configure terminal

ip access-list extended FILTRO_[DEPARTAMENTO]

 permit ip [RED_LOCAL] [WILDCARD] [RED_LOCAL] [WILDCARD]

 deny ip any [RED_VLAN_2] [WILDCARD]
 deny ip any [RED_VLAN_3] [WILDCARD]
 deny ip any [RED_VLAN_4] [WILDCARD]

 permit ip any any
exit

interface vlan [ID_VLAN]
 ip access-group FILTRO_[DEPARTAMENTO] in
exit
```

Cada VLAN debe contar con su propia ACL, modificando las redes y las máscaras wildcard según el esquema de direccionamiento implementado.

Finalmente, se recomienda verificar el funcionamiento mediante pruebas de conectividad (`ping`) entre dispositivos de la misma VLAN y comprobar que las restricciones entre departamentos se cumplen correctamente.
