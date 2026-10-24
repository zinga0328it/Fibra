//! Piccoli moduli dello sciame adattivo: nessun accesso a rete, DB o deploy.
//! Questo codice NON autentica utenti: i contesti devono arrivare da un gateway verificato.
pub mod catalog;
pub mod coordinator;
pub mod dashboard;
pub mod identity;
