import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sk_test_51PSyfKFQpmwDMxbNY99dDObf8CfPcWkt5aaHBN51skNPi1aAj9MT1Y59pPBJCMrWwcaSrOOa49VmLAPXwU2SUo8L002o7T6lqj'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_51PSyfKFQpmwDMxbNY99dDObf8CfPcWkt5aaHBN51skNPi1aAj9MT1Y59pPBJCMrWwcaSrOOa49VmLAPXwU2SUo8L002o7T6lqj'
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY') or 'pk_test_51PSyfKFQpmwDMxbNUdboNSzFeEY8qAiyBPykaV1GvELeMR565tXbJGZNwJ9c55WIy78WIhSkA0kwcdfGIDrijoh0003wwNOxoq'
