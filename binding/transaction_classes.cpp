#include "binding_common_World.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "Transaction.hpp"

namespace binding {
typedef World::transaction_type Transaction;
typedef World::base_type::base_type ParticleContainer; 
typedef ::TransactionImpl<ParticleContainer> TransactionImpl;

void register_transaction_classes()
{
    register_transaction_class<Transaction, ParticleContainer>("Transaction");
    register_transaction_impl_class<TransactionImpl, Transaction>("TransactionImpl");
}

} // namesapce binding
