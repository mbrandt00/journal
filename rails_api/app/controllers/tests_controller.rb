class TestsController < ApplicationController
  def hello_world
    render json: {message: "hello world!"}
  end
end