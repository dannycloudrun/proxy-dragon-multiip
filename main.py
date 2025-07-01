import asyncio
import os
import re

full_image = os.getenv("K_REVISION", "") or os.getenv("IMAGE", "")
match = re.search(r":(\d{1,3}(?:\.\d{1,3}){3})$", full_image)
TARGET_IP = match.group(1) if match else None
TARGET_PORT = 22

async def handle_client(reader, writer):
    if not TARGET_IP:
        writer.close()
        return

    try:
        # Leer el handshake del cliente (payload HTTP)
        data = await reader.read(1024)
        if b"Upgrade: websocket" in data or b"HTTP/1.1" in data:
            # Enviar respuesta 101 manualmente
            response = (
                b"HTTP/1.1 101 Switching Protocols\r\n"
                b"Upgrade: websocket\r\n"
                b"Connection: Upgrade\r\n"
                b"\r\n"
            )
            writer.write(response)
            await writer.drain()

        # Conexión al VPS
        remote_reader, remote_writer = await asyncio.open_connection(TARGET_IP, TARGET_PORT)

        async def pipe_to_vps():
            while True:
                chunk = await reader.read(1024)
                if not chunk:
                    break
                remote_writer.write(chunk)
                await remote_writer.drain()

        async def pipe_to_client():
            while True:
                chunk = await remote_reader.read(1024)
                if not chunk:
                    break
                writer.write(chunk)
                await writer.drain()

        await asyncio.gather(pipe_to_vps(), pipe_to_client())

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        writer.close()

async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 8080)
    print("Servidor escuchando en puerto 8080 (WebSocket + TCP)")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())

