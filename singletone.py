class SingletonInstane:
    __instance = None

    @classmethod
    def __getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__getInstance
        return cls.__instance

    @classmethod
    def add_attr(cls, test="test"):
        cls.__instance = test
    # @classmethod
    # def __str__(cls):
    #     return "singltone={}".format(cls.__instance)

    @classmethod
    def get_attr(cls, attr):
        return cls.__instance

class A(SingletonInstane):
  pass

class B(SingletonInstane):
  pass


a=SingletonInstane.instance()
a.add_attr("hi~!")

print(a.get_attr("test"))
print(B.instance())
