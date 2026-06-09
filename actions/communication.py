from utils import compose_email_flow, compose_whatsapp_flow

def handle_send_email(value, speak, listen, memory):
    compose_email_flow(speak, listen, memory)

def handle_send_whatsapp(value, speak, listen, memory):
    compose_whatsapp_flow(speak, listen, memory)
