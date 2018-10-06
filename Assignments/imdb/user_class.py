"""User class definition.
"""

class User():
  def __init__(self , username, password, email=None):
    if username == "":
      raise ValueError("Username cannot be empty")

    if password == "":
      raise ValueError("Password cannot be empty")

    self.username = username
    self.password = password
    self.email = email

  def is_authenticated(self):
    return True

  def is_active(self):
    return True

  def is_anonymous(self):
    return False

  def get_id(self):
    return str(self.username)

  def __repr__(self):
    return '<User %r, %r, %r>' % (self.username, self.email)

  def __eq__(self, other):
    if self.username == other.username and self.password == other.password:
      return True
    else:
      return False
