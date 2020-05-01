import requests
import json
import csv

merakikey = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
base_url = "https://api.meraki.com/api/v0"
orgid = "xxxxxx"

h = {
    "X-Cisco-Meraki-API-Key": merakikey,
    "Accept": "application/json",
    "Content-type": "application/json",
}

# Get a list of all networks
def network_list():
    with open("data.json") as f:
        data = json.load(f)
        network_list = []
        count = 1
        for x in data:
            if (count % 2) == 0:
                network_list.append(x["Network"])
            count += 1
    return network_list


# Loop through all Networks
for network in network_list():
    # Get info from data.json
    with open("data.json") as f:
        data = json.load(f)
        for x in data:
            if network == x["Network"]:
                if x["MX"] == "MX1":
                    mx1_name = x["MX Names"]
                    mx1_serial = x["Serial Number"]
                elif x["MX"] == "MX2":
                    mx2_name = x["MX Names"]
                    mx2_serial = x["Serial Number"]
                subnet = str(x["Subnet"])
                wan1down = x["WAN1down"]
                wan1up = x["WAN1up"]
                wan2down = x["WAN2down"]
                wan2up = x["WAN2up"]
                address = x["Address"]
                network_name = x["Network"]

    # Get a network ID by the name
    endpoint = f"/organizations/{orgid}/networks"
    response = requests.get(url=f"{base_url}{endpoint}", headers=h)
    if response.status_code == 200:
        nets = response.json()
        for net in nets:
            if net["name"] == network_name:
                netid = net["id"]

    # Claim Network Devices
    endpoint = f"/networks/{netid}/devices/claim"
    payload = {"serials": [mx1_serial, mx2_serial]}
    response = requests.post(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Claiming devices...")
    print(response.status_code)

    # Get all filtering categories
    endpoint = f"/networks/{netid}/contentFiltering/categories"
    response = requests.get(url=f"{base_url}{endpoint}", headers=h)
    if response.status_code == 200:
        full_list = response.json()

    # Open CSV file and get each category ID in a list
    new_list = []
    with open("categories.csv", "r", encoding="utf-8-sig") as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        for line in csv_reader:
            new_list.append(line[0])

    new_list_id = []
    for category in full_list["categories"]:
        if category["name"] in new_list:
            new_list_id.append(category["id"])

    # Update Category Filtering
    endpoint = f"/networks/{netid}/contentFiltering"
    payload = {"urlCategoryListSize": "fullList", "blockedUrlCategories": new_list_id}

    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Updating blocked categories...")
    print(response.status_code)

    # Update AMP
    endpoint = f"/networks/{netid}/security/malwareSettings"
    payload = {"mode": "enabled"}
    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Updating AMP...")
    print(response.status_code)

    # Update Intrusion detection and prevention
    endpoint = f"/networks/{netid}/security/intrusionSettings"
    payload = {"mode": "prevention", "idsRulesets": "balanced"}
    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Updating intrusion detection settings...")
    print(response.status_code)

    # Update Network Uplink Settings
    endpoint = f"/networks/{netid}/uplinkSettings"
    payload = {
        "bandwidthLimits": {
            "wan1": {"limitUp": wan1up, "limitDown": wan1down},
            "wan2": {"limitUp": wan2up, "limitDown": wan2down},
        }
    }
    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Updating network uplink settings...")
    print(response.status_code)

    # Update Network Site-To-Site VPN
    endpoint = f"/networks/{netid}/siteToSiteVpn"
    payload = {
        "mode": "spoke",
        "hubs": [
            {"hubId": "L_694680242521899536", "useDefaultRoute": False},
            {"hubId": "N_694680242521901854", "useDefaultRoute": False},
            {"hubId": "N_694680242521902469", "useDefaultRoute": False},
        ],
        "subnets": [{"localSubnet": f"172.21.{subnet}.0/24", "useVpn": True}],
    }
    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Updating network site-to-site VPN...")
    print(response.status_code)

    # Enable VLANs
    endpoint = f"/networks/{netid}/vlansEnabledState"
    payload = {"enabled": True}
    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Enabling VLANs...")
    print(response.status_code)

    # Create Network Vlan
    endpoint = f"/networks/{netid}/vlans/"
    payload = {
        "id": "100",
        "name": f"LAN-{network_name}",
        "applianceIp": f"172.21.{subnet}.1",
        "subnet": f"172.21.{subnet}.0/24",
    }
    response = requests.post(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Creating network VLAN...")
    print(response.status_code)

    # Update Network Vlans
    endpoint = f"/networks/{netid}/vlans/100"
    payload = {"dhcpHandling": "Do not respond to DHCP requests"}
    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Updating VLAN...")
    print(response.status_code)

    # Update Network Device MX1
    endpoint = f"/networks/{netid}/devices/{mx1_serial}"
    payload = {"name": mx1_name, "address": address}
    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Updating MX1...")
    print(response.status_code)

    # Network Warm Spare Settings
    endpoint = f"/networks/{netid}/warmSpareSettings"
    payload = {
        "enabled": True,
        "spareSerial": mx2_serial,
        "uplinkMode": "virtual",
        "virtualIp1": f"172.28.{subnet}.2",
        "virtualIp2": f"172.30.{subnet}.2",
    }
    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Configuring Warm Spare Settings...")
    print(response.status_code)

    # Update Network Device MX2
    endpoint = f"/networks/{netid}/devices/{mx2_serial}"
    payload = {"name": mx2_name, "address": address}
    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Updating MX2...")
    print(response.status_code)

    # Network SNMP Settings
    endpoint = f"/networks/{netid}/snmpSettings"
    payload = {
        "access": "users",
        "users": [{"username": "sonadmro_v3", "passphrase": "sonepar+ro!"}],
    }
    response = requests.put(
        url=f"{base_url}{endpoint}", headers=h, data=json.dumps(payload)
    )
    print("Updating SNMP Settings...")
    print(response.status_code)
