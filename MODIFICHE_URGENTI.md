# Modifiche urgenti

## URG-001 - Aggiornamento telefono cliente

Stato: da risolvere.

Il tool updateWork non aggiorna correttamente il campo telefono_cliente nel gestionale.

WR coinvolte: 103788505 (ID 627) e 103756816 (ID 628).

Verificare lo schema API, il broker MCP e la persistenza in extra_fields.telefono_cliente. Aggiungere test di regressione. I numeri corretti sono conservati nella richiesta operativa, non in questo repository pubblico.

Non modificare main. Accumulare qui le successive urgenze.
