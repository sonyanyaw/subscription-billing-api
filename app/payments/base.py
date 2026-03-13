from abc import ABC, abstractmethod


class PaymentProviderBase(ABC):

    @abstractmethod
    async def create_payment(self, invoice):
        pass