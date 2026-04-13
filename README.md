# Nayax Home Assistant Add-on

Tento repozitar obsahuje Home Assistant add-on, ktery periodicky cte data z Nayax Lynx API a publikuje je jako entity do Home Assistant.

## Co add-on umi

- nacte seznam dashboard widgetu a data z vybranych widgetu (prodeje)
- nacte seznam zarizeni (stav pripojeni automatu)
- zapise vysledky do Home Assistant entit pres Supervisor API

## Add-on

- Slozka: `nayax_telemetry`
- Nazev: Nayax Telemetry Bridge

## Token do Nayax API

Token ziskas v Nayax Core:

1. Otevri `Account Settings`.
2. Otevri zalozku `Security and Login`.
3. V sekci `User Tokens` zkopiruj token.

## Instalace do Home Assistant

1. V Home Assistant otevri `Settings -> Add-ons -> Add-on Store`.
2. Klikni na tri tecky vpravo nahore a zvol `Repositories`.
3. Pridej URL tveho forku tohoto repozitare.
4. Otevri add-on `Nayax Telemetry Bridge`, nastav konfiguraci a spust.

## Dulezite

- Nayax dashboard data se tahaji pres endpoint `POST /operational/v1/dashboard/get-widget-data`.
- `widget_ids` nastav podle tveho dashboardu (viz endpoint `GET /operational/v1/dashboard/widgets`).
- Pokud nechas `widget_ids` prazdne, addon se pokusi vybrat widgety podle nazvu (sales/revenue/vends/status/alert).
