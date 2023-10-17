import socket


def start_client():
    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setblocking(False)

    # TODO make this an easy config variable.
    server_address = ('192.168.1.120', 12345)  # Change to your needs
    return client_socket, server_address


def send_data_to_server(client_socket, server_address, message: str):
    """
    Sends pyROSe dictionary messages to your clients server.
    """
    message = message.encode()
    if message is None:
        return
    if client_socket is None:
        return
    if server_address is None:
        return

    try:
        _ = client_socket.sendto(message, server_address)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    socket, address = start_client()
    send_data_to_server(socket, address, "Hello World")
