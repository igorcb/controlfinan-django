"""Domain models. Table and column names match controlfinan-rails8-hotwire, so both apps can share the same data."""

import re
from datetime import date

import bcrypt
from django.conf import settings
from django.core import signing
from django.db import models
from django.db.models import F, Sum

EMAIL_REGEXP = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)
PASSWORD_RESET_MAX_AGE = 15 * 60  # Rails 8 has_secure_password default: 15 minutes


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(TimestampedModel):
    email_address = models.CharField(max_length=255, unique=True)
    password_digest = models.CharField(max_length=255)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email_address

    @staticmethod
    def normalize_email(value):
        return (value or "").strip().lower()

    # has_secure_password: bcrypt digests in the same "$2a$" format Rails writes.
    def set_password(self, raw):
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_COST, prefix=b"2a")
        self.password_digest = bcrypt.hashpw(raw.encode()[:72], salt).decode()

    def check_password(self, raw):
        if not raw or not self.password_digest:
            return False
        return bcrypt.checkpw(raw.encode()[:72], self.password_digest.encode())

    @classmethod
    def authenticate_by(cls, email_address, password):
        user = cls.objects.filter(email_address=cls.normalize_email(email_address)).first()
        if user is None:
            # Burn the same time as a real check to avoid user enumeration by timing.
            bcrypt.checkpw(b"x", bcrypt.hashpw(b"y", bcrypt.gensalt(rounds=settings.BCRYPT_COST)))
            return None
        return user if user.check_password(password) else None

    def validate(self, password=None, password_confirmation=None, password_required=False):
        """Returns pt-BR messages in the same order and wording as the Rails app."""
        errors = []
        if password_required and not password:
            errors.append("Senha não pode ficar em branco")
        if password is not None and password_confirmation is not None and password != password_confirmation:
            errors.append("Confirmação da senha não é igual a Senha")
        self.email_address = self.normalize_email(self.email_address)
        if not self.email_address:
            errors.append("E-mail não pode ficar em branco")
        elif not EMAIL_REGEXP.match(self.email_address):
            errors.append("E-mail não é válido")
        elif User.objects.filter(email_address=self.email_address).exclude(pk=self.pk).exists():
            errors.append("E-mail já está em uso")
        if password and len(password) < 6:
            errors.append("Senha é muito curto (mínimo: 6 caracteres)")
        return errors

    # Password reset token: signed, expires in 15 minutes and stops working once the password changes.
    def password_reset_token(self):
        return signing.TimestampSigner(salt="password_reset").sign_object({"id": self.pk, "v": self.password_digest[-10:]})

    @classmethod
    def find_by_password_reset_token(cls, token):
        try:
            data = signing.TimestampSigner(salt="password_reset").unsign_object(token, max_age=PASSWORD_RESET_MAX_AGE)
        except signing.BadSignature:
            return None
        user = cls.objects.filter(pk=data.get("id")).first()
        return user if user and user.password_digest[-10:] == data.get("v") else None


class Session(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    ip_address = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "sessions"

    def __str__(self):
        return f"Session {self.pk}"


class CurrentAccountQuerySet(models.QuerySet):
    def ordered(self):
        return self.order_by("-date_ocurrence", "-id")

    def on_date(self, day):
        return self.filter(date_ocurrence=day)

    def in_month(self, day):
        first = day.replace(day=1)
        next_month = date(first.year + first.month // 12, first.month % 12 + 1, 1)
        return self.filter(date_ocurrence__gte=first, date_ocurrence__lt=next_month)

    def rides(self):
        return self.filter(cost_id=CurrentAccount.RIDES)

    # Credits minus debits: the sign comes from type_launche (-1 or 1).
    def balance(self):
        return self.aggregate(total=Sum(F("price") * F("type_launche")))["total"] or 0

    def balance_by_day(self):
        """{date: balance}, most recent first."""
        rows = (
            self.order_by()
            .values("date_ocurrence")
            .annotate(total=Sum(F("price") * F("type_launche")))
            .order_by("-date_ocurrence")
        )
        return {row["date_ocurrence"]: row["total"] for row in rows}

    def total_by_cost(self, cost_ids):
        """{cost_id: sum of price}, only for the given categories."""
        rows = self.filter(cost_id__in=cost_ids).order_by().values("cost_id").annotate(total=Sum("price"))
        return {row["cost_id"]: row["total"] for row in rows}


class CurrentAccount(TimestampedModel):
    CASH_ACCOUNTS = {
        0: "Conta Dinheiro",
        1: "Itaú",
        2: "Santander",
        3: "CEF Poupança",
        4: "PagSeguro",
        5: "Uber",
        6: "Platinum Itaú",
        7: "Banco do Brasil",
        8: "99Pop",
    }
    COSTS = {
        0: "Combustível",
        1: "Central",
        2: "Aluguel Carro",
        3: "Almoço",
        4: "Lanche",
        5: "Diversos",
        6: "Corridas",
        7: "Telefone",
        8: "Lavagem",
        9: "Transferência",
        10: "Depósitos",
        11: "Estacionamento",
        12: "Impostos",
        13: "Multas",
        14: "Manutenção",
        15: "Viagens Uber",
    }
    TYPES = {"debito": -1, "credito": 1}
    RIDES = 6
    # Ride expenses discounted from rides in the monthly balance (legacy dashboard rule).
    RIDE_EXPENSES = {0: "Combustível", 8: "Lavagem", 7: "Telefone"}

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="current_accounts")
    cash_account_id = models.IntegerField()
    cost_id = models.IntegerField()
    date_ocurrence = models.DateField()
    type_launche = models.IntegerField()
    price = models.DecimalField(max_digits=9, decimal_places=2)
    historic = models.CharField(max_length=255, null=True, blank=True)

    objects = CurrentAccountQuerySet.as_manager()

    class Meta:
        db_table = "current_accounts"
        indexes = [models.Index(fields=["user", "date_ocurrence"], name="current_accounts_user_date_idx")]

    def __str__(self):
        return f"{self.name_cost} {self.date_ocurrence}"

    @property
    def is_credit(self):
        return self.type_launche == 1

    @property
    def type_name(self):
        """ "debito" or "credito" (the Rails enum key)."""
        return {v: k for k, v in self.TYPES.items()}.get(self.type_launche)

    @property
    def name_account(self):
        return self.CASH_ACCOUNTS.get(self.cash_account_id, "Não definido")

    @property
    def name_cost(self):
        return self.COSTS.get(self.cost_id, "Não definido")

    @property
    def type_launche_name(self):
        return "Crédito" if self.is_credit else "Débito"

    @property
    def signed_price(self):
        return self.price if self.is_credit else -self.price

    def validate(self):
        """pt-BR messages in the same order as the Rails validations."""
        errors = []
        if self.user_id is None:
            errors.append("User é obrigatório(a)")
        if self.type_launche not in self.TYPES.values():
            errors.append("Tipo não está incluído na lista")
        if self.cash_account_id not in self.CASH_ACCOUNTS:
            errors.append("Conta não está incluído na lista")
        if self.cost_id not in self.COSTS:
            errors.append("Categoria não está incluído na lista")
        if not self.date_ocurrence:
            errors.append("Data não pode ficar em branco")
        # Like Rails presence + numericality: a blank value is also "not a number".
        raw = getattr(self, "price_text", None)
        if self.price is None and not raw:
            errors += ["Valor não pode ficar em branco", "Valor não é um número"]
        elif self.price is None:
            errors.append("Valor não é um número")
        elif self.price <= 0:
            errors.append("Valor deve ser maior que 0")
        return errors
