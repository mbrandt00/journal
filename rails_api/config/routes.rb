Rails.application.routes.draw do
  Healthcheck.routes(self)
  get '/hello_world', to: 'tests#hello_world'
  # For details on the DSL available within this file, see https://guides.rubyonrails.org/routing.html
end
