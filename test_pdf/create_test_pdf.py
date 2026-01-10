from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def create_test_pdf():
    """Crea un PDF di test con dati clienti"""
    filename = "/home/aaa/fibra/test_pdf/test_clients.pdf"

    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Titolo
    title = Paragraph("Elenco Clienti - Test PDF Upload", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Cliente 1
    client1 = """
    <b>Cliente 1:</b><br/>
    Nome: Mario<br/>
    Cognome: Rossi<br/>
    Indirizzo: Via Roma 123, Roma (RM)<br/>
    Telefono: 3803645084<br/>
    """
    story.append(Paragraph(client1, styles['Normal']))
    story.append(Spacer(1, 12))

    # Cliente 2
    client2 = """
    <b>Cliente 2:</b><br/>
    Nome: Luca<br/>
    Cognome: Verdi<br/>
    Indirizzo: Via Milano 456, Milano (MI)<br/>
    Telefono: 3401234567<br/>
    """
    story.append(Paragraph(client2, styles['Normal']))
    story.append(Spacer(1, 12))

    # Cliente 3
    client3 = """
    <b>Cliente 3:</b><br/>
    Nome: Giovanni<br/>
    Cognome: Bianchi<br/>
    Indirizzo: Piazza Duomo 1, Firenze (FI)<br/>
    Telefono: 3339876543<br/>
    """
    story.append(Paragraph(client3, styles['Normal']))

    doc.build(story)
    print(f"PDF creato: {filename}")

if __name__ == "__main__":
    create_test_pdf()